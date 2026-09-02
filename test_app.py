"""
Comprehensive End-to-End Test Suite for Nature Unisex Salon
Verifies all public routes, booking flows, WhatsApp generators, contact forms,
admin authentication, dashboard views, and CRUD operations.
"""
import unittest
from app import app
from models import db, User, Service, Appointment, Gallery, Review, ContactEnquiry, WebsiteSetting

class NatureSalonTestSuite(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_01_public_pages(self):
        """Test all public pages load with HTTP 200 and contain branding elements."""
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

    def test_03_appointment_booking(self):
        """Test submitting an appointment creates a DB record and returns confirmation with WhatsApp URL."""
        test_name = 'Devanshi Sharma'
        test_data = {
            'customer_name': test_name,
            'phone': '+91 98765 11223',
            'email': 'devanshi@example.com',
            'gender': 'Women',
            'service_name': 'Signature Precision Haircut',
            'appointment_date': '2026-08-27',
            'appointment_time': '11:30 AM',
            'message': 'Please assign a senior stylist.'
        }
        response = self.client.post('/booking', data=test_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'Thank You, {test_name}!'.encode('utf-8'), response.data)
        self.assertIn(b'Continue on WhatsApp', response.data)
        self.assertIn(b'api.whatsapp.com', response.data)

        # Verify DB record
        app_record = Appointment.query.filter_by(customer_name=test_name).order_by(Appointment.created_at.desc()).first()
        self.assertIsNotNone(app_record)
        self.assertEqual(app_record.status, 'Pending')
        self.assertEqual(app_record.phone, '+91 98765 11223')
        print("[PASS] Appointment booking submission, DB storage, and WhatsApp redirect work.")

    def test_04_contact_enquiry(self):
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

    def test_05_admin_authentication_and_protection(self):
        """Test that admin pages require login, reject bad credentials, and accept valid credentials."""
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
        print("[PASS] Admin authentication, session protection, and credential checks work.")

    def test_06_admin_crud_operations(self):
        """Test admin modifying appointment status, adding services, and editing settings."""
        # Authenticate admin
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'Admin@Nature2026'})

        # 1. Update appointment status
        app_record = Appointment.query.filter_by(customer_name='Aakash Varma').first()
        self.assertIsNotNone(app_record)
        response = self.client.post(
            f'/admin/appointments/status/{app_record.id}',
            data={'status': 'Confirmed', 'admin_notes': 'Slot booked with master barber.'},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        db.session.refresh(app_record)
        self.assertEqual(app_record.status, 'Confirmed')
        self.assertEqual(app_record.admin_notes, 'Slot booked with master barber.')

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
        
        # Clean up test-created service so only authentic menu items remain in DB
        db.session.delete(svc)
        db.session.commit()

        # 3. Update Settings and then restore real production settings
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
            'google_maps_url': 'https://www.google.com/maps/place/Nature+unisex+salon/@12.9570761,77.6192442,15z/data=!4m6!3m5!1s0x3bae156290e25a91:0x923594a7d37cb230!8m2!3d12.9565087!4d77.6196044!16s%2Fg%2F11z1zkml55',
            'google_maps_embed': 'https://maps.google.com/maps?q=12.9565087,77.6196044+(Nature%20Unisex%20Salon)&t=&z=16&ie=UTF8&iwloc=B&output=embed',
            'instagram_url': 'https://www.instagram.com/nature_unisex_salon72',
            'facebook_url': '',
            'hero_headline': 'Style. Care. Confidence.',
            'hero_subtext': 'Discover bespoke hair artistry, rejuvenating skincare, and precision grooming crafted for both men and women in an atmosphere of organic calm and modern elegance.',
            'about_text': 'Nature Unisex Salon was founded on the philosophy that true beauty stems from mindful care, natural wellness, and artisan technique. We provide a hygienic, welcoming sanctuary where top-tier stylists tailor every cut, colour, and skin ritual to your unique identity.'
        }
        response = self.client.post('/admin/settings', data=settings_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # 4. Test API Endpoints
        api_booking_data = {
            'customer_name': 'Snehal Patel',
            'phone': '9876543210',
            'email': 'snehal@example.com',
            'service_id': 1,
            'appointment_date': '2026-09-05',
            'appointment_time': '14:00',
            'message': 'API test booking'
        }
        res_api = self.client.post('/api/book', json=api_booking_data)
        self.assertEqual(res_api.status_code, 200)
        self.assertTrue(res_api.get_json()['success'])

        api_enquiry_data = {
            'name': 'Kavita Menon',
            'phone': '9876543210',
            'email': 'kavita@example.com',
            'subject': 'Hydra Facial Question',
            'message': 'How long does the Hydra Facial session take?'
        }
        res_enq = self.client.post('/api/enquiry', json=api_enquiry_data)
        self.assertEqual(res_enq.status_code, 200)
        self.assertTrue(res_enq.get_json()['success'])

        # 5. Test Admin Quick-Add WhatsApp Booking
        quick_app_data = {
            'customer_name': 'Vikram Reddy',
            'phone': '9876543210',
            'gender': 'Men',
            'service_name': "Men's Hair Cut",
            'appointment_date': '2026-09-06',
            'appointment_time': '16:00',
            'status': 'Pending',
            'message': 'Direct WhatsApp Booking via +91 74837 37517'
        }
        res_quick = self.client.post('/admin/appointments/quick-add', data=quick_app_data, follow_redirects=True)
        self.assertEqual(res_quick.status_code, 200)
        quick_saved = Appointment.query.filter_by(customer_name='Vikram Reddy').first()
        self.assertIsNotNone(quick_saved)
        self.assertEqual(quick_saved.status, 'Pending')
        db.session.delete(quick_saved)
        db.session.commit()

        # 6. Test WhatsApp Webhook Endpoint
        webhook_data = {
            'name': 'Anita Rao',
            'phone': '917483737517',
            'service': 'HYDRA Facial Machine Treatment',
            'appointment_date': '2026-09-07',
            'appointment_time': '11:00',
            'message': 'Booking requested directly on WhatsApp chat'
        }
        res_hook = self.client.post('/api/whatsapp/webhook', json=webhook_data)
        self.assertEqual(res_hook.status_code, 201)
        hook_saved = Appointment.query.filter_by(customer_name='Anita Rao').first()
        self.assertIsNotNone(hook_saved)
        db.session.delete(hook_saved)
        db.session.commit()

        # 7. Test Admin Live Polling API
        res_poll = self.client.get('/api/admin/appointments/poll')
        self.assertEqual(res_poll.status_code, 200)
        self.assertTrue(res_poll.get_json()['success'])

        print("[PASS] Admin CRUD operations (status update, service add, settings update, WhatsApp quick-add, Webhook, and live polling) verified successfully.")

if __name__ == '__main__':
    unittest.main()
