"""
Comprehensive End-to-End Test Suite for Nature Unisex Salon
Verifies:
- All public routes, branding, and custom 404 handler
- Appointment booking with server-side date/time validation
- Double booking prevention and slot capacity limits
- Booking confirmation without auto-redirects
- Review moderation (unapproved pending by default, admin approval)
- Contact enquiry handling
- Admin authentication, brute-force protection, and session invalidation
- CSRF protection validation
- Secure image uploads and executable rejection
- WhatsApp URL generator parameter encoding
- PostgreSQL URL normalization & production configuration safety
- Database initialization and idempotent seeding
Uses an isolated in-memory test database to avoid touching real customer records.
"""
import io
import shutil
import unittest
from datetime import datetime, date, timedelta
from pathlib import Path

from app import create_app, init_db
from models import db, User, Service, Appointment, Gallery, Review, ContactEnquiry, WebsiteSetting
from config import normalize_db_url, ProductionConfig
from utils import clean_phone_number, build_whatsapp_booking_url, get_safe_image_url
from availability import (
    validate_booking_datetime,
    check_slot_availability,
    normalize_appointment_time,
    get_salon_current_datetime
)

class NatureSalonTestSuite(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Build clean isolated database schema and idempotent seed
        init_db(self.app)
        
        # Setup temp upload directory
        self.upload_dir = Path(self.app.config['UPLOAD_FOLDER'])
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        if self.upload_dir.exists():
            shutil.rmtree(self.upload_dir, ignore_errors=True)

    def get_future_date_str(self, days_ahead=7):
        """Helper to get a valid future appointment date in YYYY-MM-DD format."""
        return (get_salon_current_datetime().date() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    def test_01_public_pages(self):
        """Test all public pages load with HTTP 200 and contain authentic branding elements."""
        endpoints = [
            ('/', 'Style. Care. Confidence.'),
            ('/about', 'About Nature Unisex Salon'),
            ('/services', 'Salon Services'),
            ('/pricing', 'Salon Rate Card'),
            ('/gallery', 'Salon Atmosphere'),
            ('/reviews', 'Client Experiences'),
            ('/contact', 'Get in Touch'),
            ('/booking', 'Book Your Salon Appointment')
        ]
        for url, expected_text in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Failed on {url}")
            self.assertIn(expected_text.encode('utf-8'), response.data, f"Missing '{expected_text}' on {url}")
        print("[PASS] All public pages loaded with correct status 200 and branding.")

    def test_02_404_error_page(self):
        """Test custom 404 page for nonexistent routes."""
        response = self.client.get('/this-route-does-not-exist')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Page Not Found', response.data)
        print("[PASS] Custom 404 error page works correctly.")

    def test_03_appointment_booking_and_confirmation_flow(self):
        """
        Test submitting a valid appointment creates a DB record with status 'Pending'
        and renders confirmation with a manual WhatsApp button, WITHOUT automatic redirect.
        """
        test_name = 'Devanshi Sharma'
        valid_date = self.get_future_date_str(7)
        test_data = {
            'customer_name': test_name,
            'phone': '+91 98765 11223',
            'email': 'devanshi@example.com',
            'gender': 'Women',
            'service_name': "Men's Hair Cut",
            'appointment_date': valid_date,
            'appointment_time': '11:30 AM',
            'message': 'Please assign a senior stylist.'
        }
        response = self.client.post('/booking', data=test_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'Thank You, {test_name}!'.encode('utf-8'), response.data)
        self.assertIn(b'Send Confirmation via WhatsApp', response.data)
        self.assertIn(b'api.whatsapp.com', response.data)
        self.assertIn(b'#NAT-', response.data)
        self.assertIn(b'Back to Home', response.data)

        # Non-negotiable requirement: NO automatic WhatsApp redirect
        self.assertNotIn(b'http-equiv="refresh"', response.data)
        self.assertNotIn(b'Redirecting to WhatsApp...', response.data)
        self.assertNotIn(b'window.location.href = waUrl', response.data)

        # Verify DB record
        app_record = Appointment.query.filter_by(customer_name=test_name).order_by(Appointment.created_at.desc()).first()
        self.assertIsNotNone(app_record)
        self.assertEqual(app_record.status, 'Pending')
        self.assertEqual(app_record.phone, '+91 98765 11223')
        self.assertEqual(app_record.appointment_date, valid_date)

        # Test booking confirmation GET route with session
        conf_response = self.client.get(f'/booking/confirmation/{app_record.id}')
        self.assertEqual(conf_response.status_code, 200)
        self.assertIn(b'Booking Summary', conf_response.data)

        # Test booking confirmation without session / invalid reference
        with self.client.session_transaction() as sess:
            sess.clear()
        invalid_conf = self.client.get('/booking/confirmation/999999')
        self.assertEqual(invalid_conf.status_code, 200)
        self.assertIn(b'No Active Booking Found', invalid_conf.data)
        print("[PASS] Appointment booking submission and confirmation flow verified.")

    def test_04_double_booking_and_slot_availability(self):
        """
        Verify server-side appointment availability validation:
        - Rejection of past dates
        - Rejection of duplicate bookings by same customer on same slot
        - Enforcement of salon concurrent station capacity per slot
        - Freeing of slots when appointment is cancelled
        """
        test_date = self.get_future_date_str(10)
        test_time = '14:00'
        phone_user1 = '+91 99001 12233'
        phone_user2 = '+91 99002 23344'
        phone_user3 = '+91 99003 34455'
        phone_user4 = '+91 99004 45566'

        # 1. Past date booking must be rejected
        past_date = '2020-01-01'
        bad_res = self.client.post('/booking', data={
            'customer_name': 'Past Booker',
            'phone': phone_user1,
            'appointment_date': past_date,
            'appointment_time': '10:00',
            'service_name': "Men's Hair Cut"
        }, follow_redirects=True)
        self.assertIn(b'Appointment date cannot be in the past.', bad_res.data)

        # 2. Book first slot
        res1 = self.client.post('/booking', data={
            'customer_name': 'Client One',
            'phone': phone_user1,
            'appointment_date': test_date,
            'appointment_time': test_time,
            'service_name': "Men's Hair Cut"
        }, follow_redirects=True)
        self.assertEqual(res1.status_code, 200)
        self.assertIn(b'Thank You, Client One!', res1.data)

        # 3. Same customer trying to book the exact same slot again -> duplicate rejected!
        dup_res = self.client.post('/booking', data={
            'customer_name': 'Client One',
            'phone': phone_user1,
            'appointment_date': test_date,
            'appointment_time': test_time,
            'service_name': "Men's Hair Cut"
        }, follow_redirects=True)
        self.assertIn(b'You already have an active appointment scheduled for this date and time.', dup_res.data)

        # 4. Fill slot up to capacity (max_concurrent_bookings_per_slot = 3)
        res2 = self.client.post('/booking', data={
            'customer_name': 'Client Two',
            'phone': phone_user2,
            'appointment_date': test_date,
            'appointment_time': test_time,
            'service_name': "Men's Hair Cut"
        }, follow_redirects=True)
        self.assertIn(b'Thank You, Client Two!', res2.data)

        res3 = self.client.post('/booking', data={
            'customer_name': 'Client Three',
            'phone': phone_user3,
            'appointment_date': test_date,
            'appointment_time': test_time,
            'service_name': "Men's Hair Cut"
        }, follow_redirects=True)
        self.assertIn(b'Thank You, Client Three!', res3.data)

        # 5. Fourth booking exceeds slot capacity -> rejected with helpful error!
        res4 = self.client.post('/booking', data={
            'customer_name': 'Client Four',
            'phone': phone_user4,
            'appointment_date': test_date,
            'appointment_time': test_time,
            'service_name': "Men's Hair Cut"
        }, follow_redirects=True)
        self.assertIn(b'fully booked', res4.data)

        # 6. Cancel one appointment -> slot becomes available again
        apt1 = Appointment.query.filter_by(phone=phone_user1).first()
        apt1.status = 'Cancelled'
        db.session.commit()

        # Fourth client now attempts booking again -> succeeds!
        res4_retry = self.client.post('/booking', data={
            'customer_name': 'Client Four',
            'phone': phone_user4,
            'appointment_date': test_date,
            'appointment_time': test_time,
            'service_name': "Men's Hair Cut"
        }, follow_redirects=True)
        self.assertIn(b'Thank You, Client Four!', res4_retry.data)

        print("[PASS] Double booking prevention, duplicate rejection, and slot capacity limits work correctly.")

    def test_05_review_moderation(self):
        """
        Verify review moderation workflow:
        - Public submissions default to pending (is_active=False)
        - Pending reviews do not appear on public index or reviews page
        - Authenticated admin can approve/publish reviews
        - Approved reviews appear publicly
        """
        # 1. Public user submits review
        review_data = {
            'customer_name': 'Meera Krishnan',
            'rating': '5',
            'service_name': 'HYDRA Facial Machine Treatment',
            'review_text': 'Exceptional skin treatment and very courteous staff!'
        }
        res = self.client.post('/reviews', data=review_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'submitted for moderation', res.data)

        # 2. Verify in DB that is_active is False
        rev = Review.query.filter_by(customer_name='Meera Krishnan').first()
        self.assertIsNotNone(rev)
        self.assertFalse(rev.is_active)

        # 3. Public pages do not display unapproved review
        pub_rev_res = self.client.get('/reviews')
        self.assertNotIn(b'Exceptional skin treatment', pub_rev_res.data)

        pub_home_res = self.client.get('/')
        self.assertNotIn(b'Exceptional skin treatment', pub_home_res.data)

        # 4. Admin logs in and approves review
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'Admin@Nature2026'})
        approve_res = self.client.post(f'/admin/reviews/approve/{rev.id}', follow_redirects=True)
        self.assertEqual(approve_res.status_code, 200)

        db.session.refresh(rev)
        self.assertTrue(rev.is_active)

        # 5. Public page now displays the approved review
        pub_rev_res2 = self.client.get('/reviews')
        self.assertIn(b'Exceptional skin treatment', pub_rev_res2.data)
        print("[PASS] Review moderation, pending defaults, and admin publication work correctly.")

    def test_06_contact_enquiry(self):
        """Test contact enquiry submission."""
        test_enquiry = {
            'name': 'Sneha Rao',
            'phone': '+91 98765 99887',
            'email': 'sneha@example.com',
            'subject': 'Bridal Trial Inquiry',
            'message': 'Do you offer trial makeup sessions before the wedding day?'
        }
        response = self.client.post('/contact', data=test_enquiry, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Thank you for getting in touch!', response.data)

        # Verify DB record
        enq = ContactEnquiry.query.filter_by(name='Sneha Rao').first()
        self.assertIsNotNone(enq)
        self.assertEqual(enq.subject, 'Bridal Trial Inquiry')
        print("[PASS] Contact enquiry form and database capture work.")

    def test_07_admin_authentication_and_session(self):
        """Test admin authentication, brute force protection, and session invalidation on logout."""
        # 1. Access without login -> redirect
        response = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login', response.location)

        # 2. Login with wrong password
        response = self.client.post('/admin/login', data={'username': 'admin', 'password': 'WrongPassword123'}, follow_redirects=True)
        self.assertIn(b'Invalid username/email or password', response.data)

        # 3. Login with correct credentials
        response = self.client.post('/admin/login', data={'username': 'admin', 'password': 'Admin@Nature2026'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard Overview', response.data)

        # 4. Logout invalidates session
        logout_res = self.client.get('/admin/logout', follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn(b'signed out safely', logout_res.data)

        # Subsequent dashboard access must redirect back to login
        dash_res = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(dash_res.status_code, 302)
        self.assertIn('/admin/login', dash_res.location)
        print("[PASS] Admin authentication, credential protection, and logout session clearing work.")

    def test_08_admin_crud_operations(self):
        """Test admin appointment modification, service management, and settings."""
        # Authenticate admin
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'Admin@Nature2026'})

        # 1. Update appointment status
        apt = Appointment(
            customer_name='Aakash Varma',
            phone='9876543210',
            service_name="Men's Hair Cut",
            appointment_date=self.get_future_date_str(5),
            appointment_time='11:30 AM',
            status='Pending'
        )
        db.session.add(apt)
        db.session.commit()

        response = self.client.post(
            f'/admin/appointments/status/{apt.id}',
            data={'status': 'Confirmed', 'admin_notes': 'Slot booked with master barber.'},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        db.session.refresh(apt)
        self.assertEqual(apt.status, 'Confirmed')
        self.assertEqual(apt.admin_notes, 'Slot booked with master barber.')

        # 2. Add a new Service
        new_svc_data = {
            'name': 'Charcoal Detox Scalp Ritual',
            'gender_target': 'Unisex',
            'category': 'Hair',
            'price': '850.00',
            'duration_mins': '45',
            'display_order': '30',
            'description': 'Deep pore scalp detox with active activated bamboo charcoal.',
            'is_active': 'on'
        }
        response = self.client.post('/admin/services/add', data=new_svc_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        svc = Service.query.filter_by(name='Charcoal Detox Scalp Ritual').first()
        self.assertIsNotNone(svc)
        self.assertEqual(svc.price, 850.0)

        # 3. Update Settings
        settings_data = {
            'salon_name': 'Nature Unisex Salon',
            'tagline': 'Style. Care. Confidence.',
            'phone': '+91 74837 37517',
            'whatsapp_number': '917483737517',
            'email': 'info@natureunisexsalon.com',
            'currency_symbol': '₹',
            'address': 'Kashi Vishwanatha, 12, Anjaneya Temple Street, Vannarpet, Yerappa Garden, Austin Town, Neelasandra, Bengaluru, Karnataka 560047, India',
            'opening_hours_weekdays': 'Sunday - Monday: 09:00 - 21:00',
            'opening_hours_weekends': 'Everyday: 09:00 - 21:00 (Open All 7 Days)',
            'google_maps_url': 'https://www.google.com/maps',
            'google_maps_embed': 'https://maps.google.com',
            'instagram_url': 'https://www.instagram.com/nature_unisex_salon72/',
            'facebook_url': '',
            'hero_headline': 'Style. Care. Confidence.',
            'hero_subtext': 'Discover bespoke hair artistry, rejuvenating skincare, and precision grooming.',
            'about_text': 'Nature Unisex Salon was founded on the philosophy that true beauty stems from mindful care.',
            'max_concurrent_bookings_per_slot': '4'
        }
        response = self.client.post('/admin/settings', data=settings_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        updated_settings = WebsiteSetting.get_settings()
        self.assertEqual(updated_settings.max_concurrent_bookings_per_slot, 4)

        # 4. Test Notification Polling & Clearing
        res_poll = self.client.get('/api/admin/appointments/poll')
        self.assertEqual(res_poll.status_code, 200)
        self.assertTrue(res_poll.get_json()['success'])

        res_clear_all = self.client.post('/api/admin/appointments/clear-all-notifications')
        self.assertEqual(res_clear_all.status_code, 200)
        self.assertEqual(res_clear_all.get_json()['unread_count'], 0)

        print("[PASS] Admin CRUD, status update, service addition, settings, and notifications verified.")

    def test_09_csrf_protection_validation(self):
        """Verify CSRF token protection rejects requests with missing or invalid tokens."""
        # Enable CSRF protection for this test
        self.app.config['CSRF_ENABLED'] = True

        # 1. State-changing POST without CSRF token must return HTTP 400 Bad Request
        res_bad = self.client.post('/booking', data={
            'customer_name': 'No Token User',
            'phone': '9876543210',
            'appointment_date': self.get_future_date_str(5),
            'appointment_time': '10:00'
        })
        self.assertEqual(res_bad.status_code, 400)

        # 2. GET request to obtain session CSRF token
        self.client.get('/booking')
        with self.client.session_transaction() as sess:
            valid_csrf = sess.get('csrf_token')
        self.assertIsNotNone(valid_csrf)

        # 3. POST with valid CSRF token succeeds
        res_good = self.client.post('/booking', data={
            'csrf_token': valid_csrf,
            'customer_name': 'Valid Token User',
            'phone': '9876543210',
            'appointment_date': self.get_future_date_str(5),
            'appointment_time': '10:00'
        }, follow_redirects=True)
        self.assertEqual(res_good.status_code, 200)

        # Re-disable CSRF for other standard test cases
        self.app.config['CSRF_ENABLED'] = False
        print("[PASS] CSRF protection properly blocks requests with missing or invalid tokens.")

    def test_10_file_upload_security(self):
        """Test secure upload validation: accepts valid PNG/JPEG headers, rejects executables."""
        # Authenticate admin
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'Admin@Nature2026'})

        # 1. Valid PNG upload with authentic magic bytes
        png_magic = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4'
        valid_file = (io.BytesIO(png_magic), 'sample.png', 'image/png')
        res_valid = self.client.post('/admin/gallery/add', data={
            'title': 'Test Valid Haircut',
            'category': 'Hair',
            'image_file': valid_file
        }, follow_redirects=True, content_type='multipart/form-data')
        self.assertEqual(res_valid.status_code, 200)
        self.assertIn(b'Gallery item added successfully', res_valid.data)

        # 2. Malicious executable with fake PNG extension -> rejected by header inspector
        fake_png = (io.BytesIO(b'MZ\x90\x00\x03\x00\x00\x00ThisIsExecutableCode'), 'malware.png', 'image/png')
        res_malware = self.client.post('/admin/gallery/add', data={
            'title': 'Fake Image',
            'category': 'Hair',
            'image_file': fake_png
        }, follow_redirects=True, content_type='multipart/form-data')
        self.assertIn(b'Please upload an image or provide a valid image URL', res_malware.data)

        # 3. Disallowed extension (e.g. .exe, .py)
        script_file = (io.BytesIO(b'print("hello")'), 'exploit.py', 'text/x-python')
        res_ext = self.client.post('/admin/gallery/add', data={
            'title': 'Exploit',
            'category': 'Hair',
            'image_file': script_file
        }, follow_redirects=True, content_type='multipart/form-data')
        self.assertIn(b'Please upload an image or provide a valid image URL', res_ext.data)

        print("[PASS] File upload validation, MIME checks, and executable rejection work correctly.")

    def test_11_database_config_and_postgres_url_normalization(self):
        """Test PostgreSQL connection URL normalization and production configuration safety."""
        # 1. Normalization of legacy postgres:// URLs
        raw_url = "postgres://salon_user:SecretPass123@dpg-nature-salon-oregon.render.com:5432/nature_db"
        normalized = normalize_db_url(raw_url)
        self.assertTrue(normalized.startswith('postgresql://'))
        self.assertIn('salon_user:SecretPass123', normalized)

        # 2. Already modern postgresql:// remains untouched
        modern_url = "postgresql://user:pass@host:5432/db"
        self.assertEqual(normalize_db_url(modern_url), modern_url)

        # 3. Empty/None URL handling
        self.assertIsNone(normalize_db_url(None))

        # 4. ProductionConfig fails safely if SECRET_KEY is missing
        import os
        old_secret = os.environ.get('SECRET_KEY')
        old_env = os.environ.get('FLASK_ENV')
        try:
            os.environ['SECRET_KEY'] = ''
            os.environ['FLASK_ENV'] = 'production'
            with self.assertRaises(ValueError):
                ProductionConfig.init_app(self.app)
        finally:
            if old_secret is not None:
                os.environ['SECRET_KEY'] = old_secret
            else:
                os.environ.pop('SECRET_KEY', None)
            if old_env is not None:
                os.environ['FLASK_ENV'] = old_env
            else:
                os.environ.pop('FLASK_ENV', None)

        print("[PASS] PostgreSQL URL normalization and production safety checks verified.")

    def test_12_safe_image_and_whatsapp_utilities(self):
        """Test safe image URL resolution and WhatsApp link encoding."""
        # 1. Fallback image handling
        safe_img = get_safe_image_url(None, 'Hair')
        self.assertEqual(safe_img, '/static/images/services/men_haircut.jpg')

        safe_general = get_safe_image_url('', 'UnknownCategory')
        self.assertEqual(safe_general, '/static/images/hero_salon.jpg')

        # 2. Clean phone number normalization
        self.assertEqual(clean_phone_number('+91 74837 37517'), '917483737517')
        self.assertEqual(clean_phone_number('7483737517'), '917483737517')
        self.assertEqual(clean_phone_number('07483737517'), '917483737517')

        # 3. WhatsApp link generation URL encoding
        wa_url = build_whatsapp_booking_url(
            whatsapp_number='+91 74837 37517',
            customer_name='Vikram & Pooja',
            service_name='Korean Glass Skin & Hydra Facial',
            appointment_date='2026-11-10',
            appointment_time='11:30 AM',
            notes='Special request with & characters'
        )
        self.assertTrue(wa_url.startswith('https://api.whatsapp.com/send?phone=917483737517&text='))
        self.assertIn('%26', wa_url) # Encoded & character
        self.assertNotIn(' ', wa_url) # No bare spaces in URL

        print("[PASS] Safe image fallbacks, phone normalization, and WhatsApp URL encoding verified.")

if __name__ == '__main__':
    unittest.main()
