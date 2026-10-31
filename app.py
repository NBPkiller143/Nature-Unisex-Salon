import os
import time
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, session, send_from_directory, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from config import config, ProductionConfig
from models import db, User, Service, Appointment, Gallery, Review, ContactEnquiry, WebsiteSetting
from utils import (
    save_uploaded_image, 
    build_whatsapp_booking_url, 
    build_whatsapp_general_url, 
    build_whatsapp_enquiry_url, 
    build_whatsapp_direct_chat_url,
    build_whatsapp_admin_confirmation_url,
    build_whatsapp_admin_reminder_url,
    build_whatsapp_admin_review_url,
    clean_phone_number,
    sanitize_text,
    sanitize_email,
    get_safe_image_url
)
from csrf import generate_csrf_token, validate_csrf_token, get_request_csrf_token
from availability import (
    validate_booking_datetime,
    check_slot_availability,
    lock_slot_for_transaction,
    normalize_appointment_time,
    get_salon_current_datetime
)
from seed_data import seed_database

# In-memory rate limiting tracking for admin login brute-force defense
login_failed_attempts = defaultdict(list)

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        
    app = Flask(__name__)
    config_obj = config.get(config_name, config['default'])
    app.config.from_object(config_obj)

    # Dynamic static file serving: seamlessly serves uploaded files from UPLOAD_FOLDER
    # (such as a Render Persistent Disk mounted at /var/data/uploads) or default static/
    original_static_view = app.view_functions['static']
    def custom_static_view(filename, **kwargs):
        if filename.startswith('uploads/'):
            upload_subpath = filename[len('uploads/'):]
            upload_dir = Path(app.config['UPLOAD_FOLDER']).resolve()
            target_file = (upload_dir / upload_subpath).resolve()
            if target_file.is_file():
                return send_from_directory(upload_dir, upload_subpath)
        return original_static_view(filename=filename, **kwargs)
    app.view_functions['static'] = custom_static_view
    
    # Run production validation checks
    if config_name == 'production' or (hasattr(config_obj, 'init_app') and not app.config.get('TESTING')):
        ProductionConfig.init_app(app)
        try:
            from werkzeug.middleware.proxy_fix import ProxyFix
            app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
        except Exception:
            pass
        
    # Dynamic upload folder override from environment if provided
    if os.environ.get('UPLOAD_DIR'):
        app.config['UPLOAD_FOLDER'] = Path(os.environ['UPLOAD_DIR']).resolve()

    # Ensure upload directory and instance directory exist
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    instance_dir = Path(app.root_path) / 'instance'
    instance_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'admin_login'
    login_manager.login_message = 'Please sign in to access the Salon Admin Dashboard.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # CSRF Protection Middleware
    @app.before_request
    def check_csrf_protection():
        if not app.config.get('CSRF_ENABLED', True):
            return
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return
        # Whitelisted external webhooks (verified via external signature/token)
        if request.path.startswith('/api/whatsapp/webhook'):
            return
            
        token = get_request_csrf_token()
        if not validate_csrf_token(token):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'CSRF token missing or invalid. Please refresh the page and try again.'
                }), 400
            abort(400, description="CSRF validation failed. Missing or invalid security token.")

    # Jinja Custom Filters
    @app.template_filter('datetime_format')
    def datetime_format_filter(value, format='%d %b %Y, %I:%M %p'):
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except Exception:
                return value
        return value.strftime(format)

    @app.template_filter('currency')
    def currency_filter(amount):
        try:
            val = float(amount)
            if val.is_integer():
                return f"₹{int(val)}"
            return f"₹{val:.2f}"
        except Exception:
            return f"₹{amount}"

    @app.template_filter('safe_img')
    def safe_img_filter(image_url, category=None):
        return get_safe_image_url(image_url, category)

    @app.template_filter('clean_wa_phone')
    def clean_wa_phone_filter(phone_str):
        return clean_phone_number(phone_str)

    @app.template_filter('tel_link')
    def tel_link_filter(phone_str):
        if not phone_str:
            return '+917483737517'
        digits = "".join(filter(str.isdigit, str(phone_str)))
        if len(digits) == 10:
            return f"+91{digits}"
        elif len(digits) > 10 and not phone_str.strip().startswith('+'):
            return f"+{digits}"
        return phone_str.replace(' ', '')

    # HTTP Security Headers Middleware (OWASP Top 10 Hardening)
    @app.after_request
    def apply_security_headers(response):
        if response.content_type and 'text/html' in response.content_type:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https: blob:; "
            "frame-src https://www.google.com https://maps.google.com; "
            "connect-src 'self' https://api.whatsapp.com;"
        )
        return response
    
    # Inject global settings and helper data into all templates
    @app.context_processor
    def inject_global_data():
        try:
            settings = WebsiteSetting.get_settings()
            nav_services = Service.query.filter_by(is_active=True).order_by(Service.display_order.asc()).limit(8).all()
        except Exception:
            settings = None
            nav_services = []
            
        salon_wa = settings.whatsapp_number if (settings and settings.whatsapp_number) else '917483737517'
        whatsapp_url = build_whatsapp_general_url(salon_wa)
        clean_salon_phone = clean_phone_number(settings.phone if settings else '917483737517')
        
        unread_appointments_count = 0
        unread_appointments_list = []
        try:
            unread_appointments_count = Appointment.query.filter_by(is_read=False).count()
            unread_appointments_list = Appointment.query.filter_by(is_read=False).order_by(Appointment.created_at.desc()).limit(10).all()
        except Exception:
            pass

        min_date = get_salon_current_datetime().strftime('%Y-%m-%d')

        return {
            'settings': settings,
            'nav_services': nav_services,
            'current_year': datetime.now().year,
            'min_date': min_date,
            'csrf_token': generate_csrf_token,
            'whatsapp_chat_url': whatsapp_url,
            'salon_clean_phone': clean_salon_phone,
            'build_whatsapp_direct_chat_url': build_whatsapp_direct_chat_url,
            'build_whatsapp_admin_confirmation_url': build_whatsapp_admin_confirmation_url,
            'build_whatsapp_admin_reminder_url': build_whatsapp_admin_reminder_url,
            'build_whatsapp_admin_review_url': build_whatsapp_admin_review_url,
            'unread_appointments_count': unread_appointments_count,
            'unread_appointments_list': unread_appointments_list
        }

    # ==========================================
    # PUBLIC ROUTES
    # ==========================================
    
    @app.route('/')
    def index():
        """Home page with hero, featured services, gallery highlights, and verified customer reviews."""
        try:
            featured_services = Service.query.filter_by(is_active=True).order_by(Service.display_order.asc()).limit(6).all()
        except Exception:
            try:
                init_db(app)
                featured_services = Service.query.filter_by(is_active=True).order_by(Service.display_order.asc()).limit(6).all()
            except Exception:
                featured_services = []

        try:
            gallery_items = Gallery.query.filter_by(is_active=True).order_by(Gallery.created_at.desc()).limit(6).all()
        except Exception:
            gallery_items = []

        try:
            reviews = Review.query.filter_by(is_active=True).order_by(Review.display_order.asc(), Review.created_at.desc()).limit(6).all()
        except Exception:
            reviews = []

        categories = ['Hair', 'Skin', 'Grooming', 'Makeup', 'Bridal', 'Packages']
        return render_template(
            'index.html',
            featured_services=featured_services,
            gallery_items=gallery_items,
            reviews=reviews,
            categories=categories
        )

    @app.route('/about')
    def about():
        """About Nature Unisex Salon page."""
        return render_template('about.html')

    @app.route('/services')
    def services():
        """Full services page with category and gender filtering."""
        gender_filter = request.args.get('gender', 'all')
        category_filter = request.args.get('category', 'all')
        
        query = Service.query.filter_by(is_active=True)
        if gender_filter != 'all':
            query = query.filter((Service.gender_target == gender_filter) | (Service.gender_target == 'Unisex'))
        if category_filter != 'all':
            query = query.filter_by(category=category_filter)
            
        try:
            services_list = query.order_by(Service.gender_target.asc(), Service.display_order.asc()).all()
            all_services = Service.query.filter_by(is_active=True).all()
            categories = sorted(list(set(s.category for s in all_services)))
        except Exception:
            try:
                init_db(app)
                all_services = Service.query.filter_by(is_active=True).all()
                categories = sorted(list(set(s.category for s in all_services)))
                services_list = all_services[:12]
            except Exception:
                services_list = []
                categories = ['Hair', 'Skin', 'Grooming', 'Makeup', 'Bridal', 'Packages']
        
        return render_template(
            'services.html',
            services=services_list,
            categories=categories,
            active_gender=gender_filter,
            active_category=category_filter
        )

    @app.route('/pricing')
    def pricing():
        """Pricing and rate card page."""
        men_services = Service.query.filter_by(is_active=True, gender_target='Men').order_by(Service.display_order.asc()).all()
        women_services = Service.query.filter_by(is_active=True, gender_target='Women').order_by(Service.display_order.asc()).all()
        unisex_services = Service.query.filter_by(is_active=True, gender_target='Unisex').order_by(Service.display_order.asc()).all()
        packages = Service.query.filter_by(is_active=True, category='Packages').order_by(Service.display_order.asc()).all()
        
        return render_template(
            'pricing.html',
            men_services=men_services,
            women_services=women_services,
            unisex_services=unisex_services,
            packages=packages
        )

    @app.route('/gallery')
    def gallery():
        """Public gallery with category filters and lightbox preview."""
        category_filter = request.args.get('category', 'all')
        query = Gallery.query.filter_by(is_active=True)
        if category_filter != 'all':
            query = query.filter_by(category=category_filter)
            
        gallery_items = query.order_by(Gallery.created_at.desc()).all()
        categories = ['All', 'Hair', 'Makeup', 'Bridal', 'Grooming', 'Interior', 'Transformations']
        return render_template(
            'gallery.html',
            gallery_items=gallery_items,
            categories=categories,
            active_category=category_filter
        )

    @app.route('/reviews', methods=['GET', 'POST'])
    def reviews():
        """
        Customer testimonials & review submission.
        New customer reviews default to pending moderation (is_active=False).
        Public page displays ONLY approved reviews (is_active=True).
        """
        if request.method == 'POST':
            # Basic honeypot anti-spam check
            if request.form.get('honeypot'):
                flash('Your review has been received.', 'success')
                return redirect(url_for('reviews'))
                
            name = sanitize_text(request.form.get('customer_name', ''), max_length=80)
            rating_val = request.form.get('rating', '5')
            try:
                rating = int(rating_val)
            except (ValueError, TypeError):
                rating = 5
            review_text = sanitize_text(request.form.get('review_text', ''), max_length=1500)
            service_name = sanitize_text(request.form.get('service_name', ''), max_length=100)
            
            if not name or not review_text:
                flash('Please provide your name and review details.', 'error')
                return redirect(url_for('reviews'))
                
            # Strictly default to pending (is_active=False); ignore any forged form fields
            new_review = Review(
                customer_name=name,
                rating=min(max(rating, 1), 5),
                review_text=review_text,
                service_name=service_name,
                is_active=False
            )
            db.session.add(new_review)
            db.session.commit()
            flash('Thank you for sharing your experience! Your review has been submitted for moderation and will appear once approved by our salon team.', 'success')
            return redirect(url_for('reviews'))
            
        # Display only approved active reviews publicly
        reviews_list = Review.query.filter_by(is_active=True).order_by(Review.display_order.asc(), Review.created_at.desc()).all()
        services = Service.query.filter_by(is_active=True).order_by(Service.name.asc()).all()
        return render_template('reviews.html', reviews=reviews_list, services=services)

    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """Contact page with salon location, hours, and enquiry form."""
        settings = WebsiteSetting.get_settings()
        enquiry_whatsapp_url = None
        
        if request.method == 'POST':
            name = sanitize_text(request.form.get('name', ''), max_length=80)
            phone = sanitize_text(request.form.get('phone', ''), max_length=25)
            email = sanitize_email(request.form.get('email', ''))
            subject = sanitize_text(request.form.get('subject', 'General Salon Inquiry'), max_length=120)
            message = sanitize_text(request.form.get('message', ''), max_length=2000)
            
            if not name or not phone or not message:
                flash('Please fill in your name, phone number, and message.', 'error')
                return redirect(url_for('contact'))
                
            enquiry = ContactEnquiry(
                name=name,
                phone=phone,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(enquiry)
            db.session.commit()
            
            enquiry_whatsapp_url = build_whatsapp_enquiry_url(
                whatsapp_number=settings.whatsapp_number if settings else '917483737517',
                name=name,
                phone=phone,
                subject=subject,
                message=message
            )
            
            flash('Thank you for getting in touch! We have received your inquiry. You can also send it directly via WhatsApp below.', 'success')
            return render_template('contact.html', enquiry_submitted=True, enquiry_whatsapp_url=enquiry_whatsapp_url)
            
        return render_template('contact.html')

    @app.route('/api/enquiry', methods=['POST'])
    def api_enquiry():
        """AJAX endpoint for instant enquiry submission and WhatsApp link generation."""
        data = request.get_json(silent=True) or request.form
        name = sanitize_text(data.get('name', ''), max_length=80)
        phone = sanitize_text(data.get('phone', ''), max_length=25)
        email = sanitize_email(data.get('email', ''))
        subject = sanitize_text(data.get('subject', 'General Salon Inquiry'), max_length=120)
        message = sanitize_text(data.get('message', ''), max_length=2000)
        
        if not name or not phone or not message:
            return jsonify({'success': False, 'message': 'Please fill all required fields (Name, Phone, Message).'}), 400
            
        enquiry = ContactEnquiry(
            name=name,
            phone=phone,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(enquiry)
        db.session.commit()
        
        settings = WebsiteSetting.get_settings()
        whatsapp_url = build_whatsapp_enquiry_url(
            whatsapp_number=settings.whatsapp_number if settings else '917483737517',
            name=name,
            phone=phone,
            subject=subject,
            message=message
        )
        
        return jsonify({
            'success': True,
            'message': 'Your enquiry has been logged successfully.',
            'whatsapp_url': whatsapp_url
        })

    @app.route('/booking', methods=['GET', 'POST'])
    def booking():
        """
        Appointment booking page with server-side validation against past dates,
        slot capacity, duplicate bookings, and concurrency locking.
        """
        preselected_service_id = request.args.get('service_id', type=int)
        services = Service.query.filter_by(is_active=True).order_by(Service.gender_target.asc(), Service.name.asc()).all()
        settings = WebsiteSetting.get_settings()
        
        if request.method == 'POST':
            name = sanitize_text(request.form.get('customer_name', ''), max_length=80)
            phone = sanitize_text(request.form.get('phone', ''), max_length=25)
            email = sanitize_email(request.form.get('email', ''))
            gender = sanitize_text(request.form.get('gender', 'Not Specified'), max_length=30)
            service_id = request.form.get('service_id', type=int)
            service_name = sanitize_text(request.form.get('service_name', ''), max_length=120)
            app_date = sanitize_text(request.form.get('appointment_date', ''), max_length=20)
            app_time = sanitize_text(request.form.get('appointment_time', ''), max_length=20)
            notes = sanitize_text(request.form.get('message', ''), max_length=1000)
            
            # 1. Required fields validation
            if not name or not phone or not app_date or not app_time:
                flash('Please complete all required fields (Name, Phone, Date, and Time).', 'error')
                return redirect(url_for('booking', service_id=service_id))

            # 2. Server-side Date & Time validation (rejects past dates, past times, invalid slots)
            is_valid_dt, dt_err, parsed_date, time_tuple = validate_booking_datetime(app_date, app_time)
            if not is_valid_dt:
                flash(dt_err, 'error')
                return redirect(url_for('booking', service_id=service_id))

            std_24h, disp_12h = time_tuple

            # 3. Service validation
            if service_id:
                svc_obj = Service.query.filter_by(id=service_id, is_active=True).first()
                if not svc_obj:
                    flash('The selected service is not currently available.', 'error')
                    return redirect(url_for('booking'))
                service_name = svc_obj.name
            if not service_name:
                service_name = "General Salon Consultation"

            # 4. Concurrency lock & Slot Capacity / Double Booking validation
            lock_slot_for_transaction(app_date, std_24h)
            is_avail, avail_err = check_slot_availability(app_date, std_24h, customer_phone=phone, customer_email=email)
            if not is_avail:
                flash(avail_err, 'error')
                return redirect(url_for('booking', service_id=service_id))
                
            appointment = Appointment(
                customer_name=name,
                phone=phone,
                email=email,
                gender=gender,
                service_id=service_id,
                service_name=service_name,
                appointment_date=app_date,
                appointment_time=disp_12h,
                message=notes,
                status='Pending',
                is_read=False
            )
            db.session.add(appointment)
            db.session.commit()
            
            # Store in session for secure confirmation page retrieval
            session['last_booking_id'] = appointment.id

            # Build WhatsApp direct URL (for customer manual click)
            whatsapp_url = build_whatsapp_booking_url(
                whatsapp_number=settings.whatsapp_number,
                customer_name=name,
                service_name=service_name,
                appointment_date=app_date,
                appointment_time=disp_12h,
                notes=notes
            )
            
            return render_template(
                'booking_confirmation.html',
                appointment=appointment,
                whatsapp_url=whatsapp_url
            )
            
        return render_template(
            'booking.html',
            services=services,
            preselected_service_id=preselected_service_id
        )

    @app.route('/booking/confirmation/<int:appointment_id>')
    @app.route('/booking/confirmation')
    def booking_confirmation(appointment_id=None):
        """
        Customer-facing booking confirmation page.
        Only displays details for the session's own recent booking or authenticated admins.
        Handles missing or invalid booking references gracefully without leaking data.
        """
        target_id = appointment_id or session.get('last_booking_id')
        appointment = None
        if target_id:
            # Authorized only if ID matches current session or logged-in admin
            if session.get('last_booking_id') == target_id or current_user.is_authenticated:
                appointment = db.session.get(Appointment, target_id)
        
        settings = WebsiteSetting.get_settings()
        whatsapp_url = None
        if appointment:
            whatsapp_url = build_whatsapp_booking_url(
                whatsapp_number=settings.whatsapp_number,
                customer_name=appointment.customer_name,
                service_name=appointment.service_name,
                appointment_date=appointment.appointment_date,
                appointment_time=appointment.appointment_time,
                notes=appointment.message or ""
            )
            
        return render_template(
            'booking_confirmation.html',
            appointment=appointment,
            whatsapp_url=whatsapp_url
        )

    # API Endpoints for Ajax Booking
    @app.route('/api/book', methods=['POST'])
    def api_book():
        """AJAX endpoint for instant booking with double-booking and past-date validation."""
        data = request.get_json(silent=True) or request.form
        name = sanitize_text(data.get('customer_name', ''), max_length=80)
        phone = sanitize_text(data.get('phone', ''), max_length=25)
        email = sanitize_email(data.get('email', ''))
        gender = sanitize_text(data.get('gender', 'Not Specified'), max_length=30)
        service_id = data.get('service_id')
        service_name = sanitize_text(data.get('service_name', ''), max_length=120)
        app_date = sanitize_text(data.get('appointment_date', ''), max_length=20)
        app_time = sanitize_text(data.get('appointment_time', ''), max_length=20)
        notes = sanitize_text(data.get('message', ''), max_length=1000)
        
        if not name or not phone or not app_date or not app_time:
            return jsonify({'success': False, 'message': 'Please fill all required booking fields.'}), 400

        # Validate date and time
        is_valid_dt, dt_err, parsed_date, time_tuple = validate_booking_datetime(app_date, app_time)
        if not is_valid_dt:
            return jsonify({'success': False, 'message': dt_err}), 400

        std_24h, disp_12h = time_tuple

        svc_id_int = None
        if service_id:
            try:
                svc_id_int = int(service_id)
                svc_obj = Service.query.filter_by(id=svc_id_int, is_active=True).first()
                if svc_obj:
                    service_name = svc_obj.name
                else:
                    return jsonify({'success': False, 'message': 'The selected service is not available.'}), 400
            except (ValueError, TypeError):
                pass

        if not service_name:
            service_name = "General Consultation"

        # Concurrency lock & Slot availability check
        lock_slot_for_transaction(app_date, std_24h)
        is_avail, avail_err = check_slot_availability(app_date, std_24h, customer_phone=phone, customer_email=email)
        if not is_avail:
            return jsonify({'success': False, 'message': avail_err}), 409
            
        appointment = Appointment(
            customer_name=name,
            phone=phone,
            email=email,
            gender=gender,
            service_id=svc_id_int,
            service_name=service_name,
            appointment_date=app_date,
            appointment_time=disp_12h,
            message=notes,
            status='Pending',
            is_read=False
        )
        db.session.add(appointment)
        db.session.commit()
        
        session['last_booking_id'] = appointment.id

        settings = WebsiteSetting.get_settings()
        whatsapp_url = build_whatsapp_booking_url(
            whatsapp_number=settings.whatsapp_number,
            customer_name=name,
            service_name=service_name,
            appointment_date=app_date,
            appointment_time=disp_12h,
            notes=notes
        )
        
        return jsonify({
            'success': True,
            'message': 'Thank you! Your appointment request has been received. Nature Unisex Salon will contact you shortly to confirm your booking.',
            'appointment_id': appointment.id,
            'booking_reference': appointment.booking_reference,
            'whatsapp_url': whatsapp_url
        })

    # ==========================================
    # ADMIN ROUTES
    # ==========================================

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Admin authentication login with brute-force lockout and open-redirect defense."""
        if current_user.is_authenticated:
            return redirect(url_for('admin_dashboard'))
            
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1').split(',')[0].strip()
        now = time.time()
        
        # Purge failed attempts older than 5 minutes (300 seconds)
        login_failed_attempts[client_ip] = [t for t in login_failed_attempts[client_ip] if now - t < 300]
        
        # Brute-force lockout check
        if len(login_failed_attempts[client_ip]) >= 5:
            flash('Security Notice: Too many failed login attempts from your IP. Please wait 5 minutes before trying again.', 'error')
            return render_template('admin/login.html'), 429
            
        if request.method == 'POST':
            username_or_email = sanitize_text(request.form.get('username', ''), max_length=120)
            password = request.form.get('password', '')
            remember = True if request.form.get('remember') else False
            
            user = User.query.filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            ).first()
            
            if user and user.check_password(password):
                login_failed_attempts.pop(client_ip, None) # Reset attempts on success
                login_user(user, remember=remember)
                flash(f'Welcome back, {user.username}!', 'success')
                next_page = request.args.get('next')
                # Open redirect defense: strictly ensure next_page is a local relative URI
                if next_page and (not next_page.startswith('/') or next_page.startswith('//')):
                    next_page = None
                return redirect(next_page or url_for('admin_dashboard'))
            else:
                login_failed_attempts[client_ip].append(now)
                attempts_left = max(0, 5 - len(login_failed_attempts[client_ip]))
                if attempts_left > 0:
                    flash(f'Invalid username/email or password. ({attempts_left} attempts remaining)', 'error')
                else:
                    flash('Security Notice: Too many failed login attempts. IP temporarily restricted.', 'error')
                
        return render_template('admin/login.html')

    @app.route('/admin/logout')
    @login_required
    def admin_logout():
        """Admin sign out with complete session invalidation."""
        session.clear()
        logout_user()
        flash('You have been signed out safely.', 'info')
        return redirect(url_for('admin_login'))

    @app.route('/admin')
    @app.route('/admin/')
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        """Admin overview dashboard with key metrics and recent activities."""
        total_appointments = Appointment.query.count()
        pending_appointments = Appointment.query.filter_by(status='Pending').count()
        confirmed_appointments = Appointment.query.filter_by(status='Confirmed').count()
        completed_appointments = Appointment.query.filter_by(status='Completed').count()
        
        total_services = Service.query.count()
        total_inquiries = ContactEnquiry.query.count()
        unread_inquiries = ContactEnquiry.query.filter_by(is_read=False).count()
        
        recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(8).all()
        recent_inquiries = ContactEnquiry.query.order_by(ContactEnquiry.created_at.desc()).limit(5).all()
        
        return render_template(
            'admin/dashboard.html',
            total_appointments=total_appointments,
            pending_appointments=pending_appointments,
            confirmed_appointments=confirmed_appointments,
            completed_appointments=completed_appointments,
            total_services=total_services,
            total_inquiries=total_inquiries,
            unread_inquiries=unread_inquiries,
            recent_appointments=recent_appointments,
            recent_inquiries=recent_inquiries
        )

    @app.route('/admin/appointments', methods=['GET', 'POST'])
    @login_required
    def admin_appointments():
        """Manage customer appointments."""
        status_filter = request.args.get('status', 'all')
        search_query = request.args.get('search', '').strip()
        
        query = Appointment.query
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)
        if search_query:
            query = query.filter(
                (Appointment.customer_name.ilike(f'%{search_query}%')) |
                (Appointment.phone.ilike(f'%{search_query}%')) |
                (Appointment.service_name.ilike(f'%{search_query}%'))
            )
            
        appointments = query.order_by(Appointment.created_at.desc()).all()
        services = Service.query.order_by(Service.gender_target.asc(), Service.name.asc()).all()
        return render_template(
            'admin/appointments.html',
            appointments=appointments,
            services=services,
            active_status=status_filter,
            search_query=search_query
        )

    @app.route('/admin/appointments/quick-add', methods=['POST'])
    @login_required
    def admin_quick_add_appointment():
        """Log a WhatsApp or direct phone appointment directly from admin portal."""
        name = sanitize_text(request.form.get('customer_name', ''), max_length=100)
        phone = sanitize_text(request.form.get('phone', ''), max_length=25)
        email = sanitize_email(request.form.get('email', ''))
        gender = sanitize_text(request.form.get('gender', 'Not Specified'), max_length=30)
        service_name = sanitize_text(request.form.get('service_name', 'General Service'), max_length=120)
        app_date = sanitize_text(request.form.get('appointment_date', ''), max_length=20)
        app_time = sanitize_text(request.form.get('appointment_time', ''), max_length=20)
        status = sanitize_text(request.form.get('status', 'Pending'), max_length=20)
        message = sanitize_text(request.form.get('message', ''), max_length=1000)
        admin_notes = sanitize_text(request.form.get('admin_notes', 'Logged via WhatsApp/Phone Direct'), max_length=500)

        if not name or not phone or not app_date or not app_time:
            flash('Customer Name, Phone, Date, and Time are required.', 'error')
            return redirect(url_for('admin_appointments'))

        appointment = Appointment(
            customer_name=name,
            phone=phone,
            email=email,
            gender=gender,
            service_name=service_name,
            appointment_date=app_date,
            appointment_time=app_time,
            status=status if status in ['Pending', 'Confirmed', 'Completed', 'Cancelled'] else 'Pending',
            message=message,
            admin_notes=admin_notes
        )
        db.session.add(appointment)
        db.session.commit()
        flash(f'New appointment for {name} (#{appointment.id}) has been recorded for review.', 'success')
        return redirect(url_for('admin_appointments'))

    @app.route('/admin/appointments/status/<int:appointment_id>', methods=['POST'])
    @login_required
    def admin_update_appointment_status(appointment_id):
        """Update appointment status and admin notes."""
        appointment = db.session.get(Appointment, appointment_id)
        if not appointment:
            flash('Appointment not found.', 'error')
            return redirect(url_for('admin_appointments'))
            
        new_status = request.form.get('status')
        notes = request.form.get('admin_notes')
        
        if new_status in ['Pending', 'Confirmed', 'Completed', 'Cancelled']:
            appointment.status = new_status
        if notes is not None:
            appointment.admin_notes = notes
            
        db.session.commit()
        flash(f'Appointment #{appointment.id} updated to {appointment.status}.', 'success')
        return redirect(request.referrer or url_for('admin_appointments'))

    @app.route('/admin/appointments/delete/<int:appointment_id>', methods=['POST'])
    @login_required
    def admin_delete_appointment(appointment_id):
        """Delete an appointment record."""
        appointment = db.session.get(Appointment, appointment_id)
        if appointment:
            db.session.delete(appointment)
            db.session.commit()
            flash(f'Appointment #{appointment_id} deleted.', 'success')
        return redirect(url_for('admin_appointments'))

    @app.route('/api/admin/appointments/poll')
    @login_required
    def admin_appointments_poll():
        """Live polling endpoint to check for incoming appointments and unread notifications."""
        pending_count = Appointment.query.filter_by(status='Pending').count()
        unread_query = Appointment.query.filter_by(is_read=False).order_by(Appointment.created_at.desc())
        unread_count = unread_query.count()
        unread_items = unread_query.limit(10).all()
        latest = Appointment.query.order_by(Appointment.id.desc()).first()
        latest_id = latest.id if latest else 0
        
        items_data = []
        for a in unread_items:
            items_data.append({
                'id': a.id,
                'customer_name': a.customer_name,
                'phone': a.phone,
                'service_name': a.service_name,
                'appointment_date': a.appointment_date,
                'appointment_time': a.appointment_time,
                'created_at': a.created_at.strftime('%I:%M %p, %d %b') if a.created_at else ''
            })
            
        return jsonify({
            'success': True,
            'pending_count': pending_count,
            'unread_count': unread_count,
            'latest_id': latest_id,
            'unread_appointments': items_data
        })

    @app.route('/api/admin/appointments/<int:appointment_id>/clear-notification', methods=['POST'])
    @login_required
    def admin_clear_single_notification(appointment_id):
        """Mark a single appointment notification as cleared/read."""
        appointment = db.session.get(Appointment, appointment_id)
        if appointment:
            appointment.is_read = True
            db.session.commit()
        unread_count = Appointment.query.filter_by(is_read=False).count()
        return jsonify({
            'success': True,
            'unread_count': unread_count,
            'cleared_id': appointment_id
        })

    @app.route('/api/admin/appointments/clear-all-notifications', methods=['POST'])
    @login_required
    def admin_clear_all_notifications():
        """Clear all pending appointment notifications."""
        Appointment.query.filter_by(is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({
            'success': True,
            'unread_count': 0
        })

    @app.route('/api/whatsapp/webhook', methods=['GET', 'POST'])
    def api_whatsapp_webhook():
        """
        Incoming webhook endpoint for WhatsApp integrations (Meta Cloud API, Twilio, or Zapier/n8n).
        Instantly logs incoming appointment messages directly into the website for admin review.
        """
        # GET: Webhook verification handshake
        if request.method == 'GET':
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            verify_secret = os.environ.get('WHATSAPP_VERIFY_TOKEN', 'nature_unisex_secret_2026')
            
            if mode == 'subscribe' and token == verify_secret:
                return challenge or "OK", 200
            return "Forbidden", 403

        # POST: Process incoming WhatsApp message payload
        try:
            payload = request.get_json(silent=True) or request.form.to_dict() or {}
            customer_name = sanitize_text(payload.get('name') or payload.get('customer_name') or payload.get('From') or 'WhatsApp Guest', max_length=100)
            phone = sanitize_text(payload.get('phone') or payload.get('WaId') or payload.get('From') or '', max_length=30)
            service_name = sanitize_text(payload.get('service') or payload.get('service_name') or 'WhatsApp Booking Request', max_length=120)
            app_date = sanitize_text(payload.get('date') or payload.get('appointment_date') or datetime.now().strftime('%Y-%m-%d'), max_length=20)
            app_time = sanitize_text(payload.get('time') or payload.get('appointment_time') or '09:00', max_length=20)
            message = sanitize_text(payload.get('message') or payload.get('Body') or str(payload), max_length=1000)
            
            if phone:
                appointment = Appointment(
                    customer_name=customer_name,
                    phone=phone,
                    service_name=service_name,
                    appointment_date=app_date,
                    appointment_time=app_time,
                    message=message,
                    status='Pending',
                    admin_notes='Received via WhatsApp Webhook'
                )
                db.session.add(appointment)
                db.session.commit()
                return jsonify({'success': True, 'appointment_id': appointment.id}), 201
            return jsonify({'success': True, 'message': 'Webhook received'}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

    @app.route('/admin/services')
    @login_required
    def admin_services():
        """Manage salon services catalog."""
        services = Service.query.order_by(Service.gender_target.asc(), Service.display_order.asc(), Service.name.asc()).all()
        categories = ['Hair', 'Skin', 'Grooming', 'Makeup', 'Spa', 'Bridal', 'Packages']
        return render_template('admin/services.html', services=services, categories=categories)

    @app.route('/admin/services/add', methods=['POST'])
    @login_required
    def admin_add_service():
        """Add new salon service."""
        name = request.form.get('name', '').strip()
        gender_target = request.form.get('gender_target', 'Unisex')
        category = request.form.get('category', 'Hair')
        description = request.form.get('description', '').strip()
        try:
            price = float(request.form.get('price', 0.0) or 0.0)
        except (ValueError, TypeError):
            price = 0.0
        try:
            duration_mins = int(request.form.get('duration_mins', 30) or 30)
        except (ValueError, TypeError):
            duration_mins = 30
        is_active = True if request.form.get('is_active') == 'on' else False
        try:
            display_order = int(request.form.get('display_order', 0) or 0)
        except (ValueError, TypeError):
            display_order = 0
        
        image_file = request.files.get('image_file')
        image_url = None
        if image_file and image_file.filename:
            image_url = save_uploaded_image(image_file, 'services')
            
        if not image_url:
            image_url = request.form.get('image_url', '').strip() or None
            
        new_svc = Service(
            name=name,
            gender_target=gender_target,
            category=category,
            description=description,
            price=price,
            duration_mins=duration_mins,
            image_url=image_url,
            is_active=is_active,
            display_order=display_order
        )
        db.session.add(new_svc)
        db.session.commit()
        flash(f'Service "{name}" added successfully.', 'success')
        return redirect(url_for('admin_services'))

    @app.route('/admin/services/edit/<int:service_id>', methods=['POST'])
    @login_required
    def admin_edit_service(service_id):
        """Edit an existing salon service."""
        service = db.session.get(Service, service_id)
        if not service:
            flash('Service not found.', 'error')
            return redirect(url_for('admin_services'))
            
        service.name = request.form.get('name', service.name).strip()
        service.gender_target = request.form.get('gender_target', service.gender_target)
        service.category = request.form.get('category', service.category)
        service.description = request.form.get('description', '').strip()
        try:
            service.price = float(request.form.get('price', service.price) or 0.0)
        except (ValueError, TypeError):
            pass
        try:
            service.duration_mins = int(request.form.get('duration_mins', service.duration_mins) or 30)
        except (ValueError, TypeError):
            pass
        service.is_active = True if request.form.get('is_active') == 'on' else False
        try:
            service.display_order = int(request.form.get('display_order', service.display_order) or 0)
        except (ValueError, TypeError):
            pass
        
        image_file = request.files.get('image_file')
        if image_file and image_file.filename:
            uploaded_url = save_uploaded_image(image_file, 'services')
            if uploaded_url:
                service.image_url = uploaded_url
        elif request.form.get('image_url'):
            service.image_url = request.form.get('image_url').strip()
            
        db.session.commit()
        flash(f'Service "{service.name}" updated successfully.', 'success')
        return redirect(url_for('admin_services'))

    @app.route('/admin/services/toggle/<int:service_id>', methods=['POST'])
    @login_required
    def admin_toggle_service(service_id):
        """Toggle service visibility."""
        service = db.session.get(Service, service_id)
        if service:
            service.is_active = not service.is_active
            db.session.commit()
            status_text = 'activated' if service.is_active else 'deactivated'
            flash(f'Service "{service.name}" {status_text}.', 'info')
        return redirect(url_for('admin_services'))

    @app.route('/admin/services/delete/<int:service_id>', methods=['POST'])
    @login_required
    def admin_delete_service(service_id):
        """Delete service."""
        service = db.session.get(Service, service_id)
        if service:
            db.session.delete(service)
            db.session.commit()
            flash(f'Service "{service.name}" deleted.', 'success')
        return redirect(url_for('admin_services'))

    @app.route('/admin/gallery')
    @login_required
    def admin_gallery():
        """Manage gallery images."""
        items = Gallery.query.order_by(Gallery.created_at.desc()).all()
        categories = ['Hair', 'Makeup', 'Bridal', 'Grooming', 'Interior', 'Transformations']
        return render_template('admin/gallery.html', gallery_items=items, categories=categories)

    @app.route('/admin/gallery/add', methods=['POST'])
    @login_required
    def admin_add_gallery_item():
        """Upload and add gallery photo."""
        title = request.form.get('title', '').strip() or 'Salon Showcase'
        category = request.form.get('category', 'Hair')
        image_file = request.files.get('image_file')
        image_url = request.form.get('image_url', '').strip()
        
        if image_file and image_file.filename:
            uploaded_path = save_uploaded_image(image_file, 'gallery')
            if uploaded_path:
                image_url = uploaded_path
                
        if not image_url:
            flash('Please upload an image or provide a valid image URL.', 'error')
            return redirect(url_for('admin_gallery'))
            
        item = Gallery(title=title, category=category, image_url=image_url, is_active=True)
        db.session.add(item)
        db.session.commit()
        flash('Gallery item added successfully.', 'success')
        return redirect(url_for('admin_gallery'))

    @app.route('/admin/gallery/delete/<int:item_id>', methods=['POST'])
    @login_required
    def admin_delete_gallery_item(item_id):
        """Delete a gallery item."""
        item = db.session.get(Gallery, item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
            flash('Gallery item removed.', 'success')
        return redirect(url_for('admin_gallery'))

    @app.route('/admin/reviews')
    @login_required
    def admin_reviews():
        """Manage customer testimonials and review moderation."""
        reviews = Review.query.order_by(Review.created_at.desc()).all()
        return render_template('admin/reviews.html', reviews=reviews)

    @app.route('/admin/reviews/add', methods=['POST'])
    @login_required
    def admin_add_review():
        """Add new review manually from admin dashboard (approved by default)."""
        name = request.form.get('customer_name', '').strip()
        rating = int(request.form.get('rating', 5))
        review_text = request.form.get('review_text', '').strip()
        service_name = request.form.get('service_name', '').strip()
        
        if not name or not review_text:
            flash('Please provide customer name and review text.', 'error')
            return redirect(url_for('admin_reviews'))
            
        review = Review(
            customer_name=name,
            rating=min(max(rating, 1), 5),
            review_text=review_text,
            service_name=service_name,
            is_active=True
        )
        db.session.add(review)
        db.session.commit()
        flash('Testimonial added and published successfully.', 'success')
        return redirect(url_for('admin_reviews'))

    @app.route('/admin/reviews/approve/<int:review_id>', methods=['POST'])
    @login_required
    def admin_approve_review(review_id):
        """Explicitly approve and publish a pending review."""
        review = db.session.get(Review, review_id)
        if review:
            review.is_active = True
            db.session.commit()
            flash(f'Review from "{review.customer_name}" has been approved and published to the website.', 'success')
        return redirect(url_for('admin_reviews'))

    @app.route('/admin/reviews/toggle/<int:review_id>', methods=['POST'])
    @login_required
    def admin_toggle_review(review_id):
        """Toggle review visibility between Approved/Published and Pending/Hidden."""
        review = db.session.get(Review, review_id)
        if review:
            review.is_active = not review.is_active
            db.session.commit()
            state = 'published' if review.is_active else 'hidden'
            flash(f'Review from "{review.customer_name}" is now {state}.', 'info')
        return redirect(url_for('admin_reviews'))

    @app.route('/admin/reviews/delete/<int:review_id>', methods=['POST'])
    @login_required
    def admin_delete_review(review_id):
        """Delete a review."""
        review = db.session.get(Review, review_id)
        if review:
            db.session.delete(review)
            db.session.commit()
            flash('Review deleted.', 'success')
        return redirect(url_for('admin_reviews'))

    @app.route('/admin/enquiries')
    @login_required
    def admin_enquiries():
        """Manage customer contact inquiries."""
        enquiries = ContactEnquiry.query.order_by(ContactEnquiry.created_at.desc()).all()
        return render_template('admin/enquiries.html', enquiries=enquiries)

    @app.route('/admin/enquiries/toggle-read/<int:enquiry_id>', methods=['POST'])
    @login_required
    def admin_toggle_enquiry_read(enquiry_id):
        """Mark enquiry as read or unread."""
        enquiry = db.session.get(ContactEnquiry, enquiry_id)
        if enquiry:
            enquiry.is_read = not enquiry.is_read
            db.session.commit()
        return redirect(url_for('admin_enquiries'))

    @app.route('/admin/enquiries/delete/<int:enquiry_id>', methods=['POST'])
    @login_required
    def admin_delete_enquiry(enquiry_id):
        """Delete an enquiry."""
        enquiry = db.session.get(ContactEnquiry, enquiry_id)
        if enquiry:
            db.session.delete(enquiry)
            db.session.commit()
            flash('Inquiry removed.', 'success')
        return redirect(url_for('admin_enquiries'))

    @app.route('/admin/settings', methods=['GET', 'POST'])
    @login_required
    def admin_settings():
        """Manage salon global profile and contact settings."""
        settings = WebsiteSetting.get_settings()
        
        if request.method == 'POST':
            settings.salon_name = sanitize_text(request.form.get('salon_name', settings.salon_name), max_length=100)
            settings.tagline = sanitize_text(request.form.get('tagline', settings.tagline), max_length=150)
            settings.phone = sanitize_text(request.form.get('phone', settings.phone), max_length=25)
            settings.whatsapp_number = sanitize_text(request.form.get('whatsapp_number', settings.whatsapp_number), max_length=25)
            settings.email = sanitize_email(request.form.get('email', settings.email))
            settings.address = sanitize_text(request.form.get('address', settings.address), max_length=300)
            settings.google_maps_url = sanitize_text(request.form.get('google_maps_url', settings.google_maps_url), max_length=500)
            settings.google_maps_embed = request.form.get('google_maps_embed', settings.google_maps_embed).strip()
            settings.instagram_url = sanitize_text(request.form.get('instagram_url', settings.instagram_url), max_length=250)
            settings.facebook_url = sanitize_text(request.form.get('facebook_url', settings.facebook_url), max_length=250)
            settings.opening_hours_weekdays = sanitize_text(request.form.get('opening_hours_weekdays', settings.opening_hours_weekdays), max_length=100)
            settings.opening_hours_weekends = sanitize_text(request.form.get('opening_hours_weekends', settings.opening_hours_weekends), max_length=100)
            settings.hero_headline = sanitize_text(request.form.get('hero_headline', settings.hero_headline), max_length=150)
            settings.hero_subtext = sanitize_text(request.form.get('hero_subtext', settings.hero_subtext), max_length=300)
            settings.about_text = sanitize_text(request.form.get('about_text', settings.about_text), max_length=1500)
            settings.currency_symbol = sanitize_text(request.form.get('currency_symbol', settings.currency_symbol), max_length=5)
            
            try:
                capacity_val = int(request.form.get('max_concurrent_bookings_per_slot', settings.max_concurrent_bookings_per_slot or 3))
                settings.max_concurrent_bookings_per_slot = max(1, min(capacity_val, 10))
            except (ValueError, TypeError):
                pass

            db.session.commit()
            flash('Salon website settings updated successfully!', 'success')
            return redirect(url_for('admin_settings'))
            
        return render_template('admin/settings.html', settings=settings)

    @app.route('/admin/profile', methods=['POST'])
    @login_required
    def admin_update_profile():
        """Update admin password or credentials with validation."""
        current_pwd = request.form.get('current_password', '')
        new_pwd = request.form.get('new_password', '')
        confirm_pwd = request.form.get('confirm_password', '')
        new_username = sanitize_text(request.form.get('username', ''), max_length=60)
        new_email = sanitize_email(request.form.get('email', ''))
        
        if not current_user.check_password(current_pwd):
            flash('Incorrect current password.', 'error')
            return redirect(url_for('admin_settings'))
            
        if new_pwd:
            if len(new_pwd) < 8:
                flash('New password must be at least 8 characters long for security.', 'error')
                return redirect(url_for('admin_settings'))
            if new_pwd != confirm_pwd:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('admin_settings'))
            current_user.set_password(new_pwd)
            
        if new_username:
            current_user.username = new_username
        if new_email:
            current_user.email = new_email
            
        db.session.commit()
        flash('Admin profile credentials updated successfully.', 'success')
        return redirect(url_for('admin_settings'))

    # ==========================================
    # ERROR HANDLERS (Clean non-leaking responses)
    # ==========================================
    @app.errorhandler(400)
    def bad_request(e):
        msg = getattr(e, 'description', 'Bad Request')
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': msg}), 400
        return render_template('404.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        return render_template('404.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Not Found'}), 404
        return render_template('404.html'), 404

    @app.errorhandler(409)
    def conflict_error(e):
        msg = getattr(e, 'description', 'Conflict')
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': msg}), 409
        return render_template('404.html'), 409

    @app.errorhandler(429)
    def ratelimit_handler(e):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Too Many Requests'}), 429
        return render_template('404.html'), 429

    @app.errorhandler(500)
    def internal_server_error(e):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Internal Server Error'}), 500
        return render_template('500.html'), 500

    return app

def ensure_db_schema_upgrades(engine=None):
    """Ensure newly added columns exist in existing database schemas without data loss."""
    try:
        from sqlalchemy import inspect, text
        target_engine = engine or db.engine
        inspector = inspect(target_engine)
        table_names = inspector.get_table_names()
        
        # 1. Check appointments.is_read
        if 'appointments' in table_names:
            columns = [c['name'] for c in inspector.get_columns('appointments')]
            if 'is_read' not in columns:
                with target_engine.connect() as conn:
                    conn.execute(text("ALTER TABLE appointments ADD COLUMN is_read BOOLEAN DEFAULT FALSE;"))
                    conn.commit()
                    print("[*] Schema upgrade: added 'is_read' column to 'appointments'.")

        # 2. Check website_settings.max_concurrent_bookings_per_slot
        if 'website_settings' in table_names:
            columns = [c['name'] for c in inspector.get_columns('website_settings')]
            if 'max_concurrent_bookings_per_slot' not in columns:
                with target_engine.connect() as conn:
                    conn.execute(text("ALTER TABLE website_settings ADD COLUMN max_concurrent_bookings_per_slot INTEGER DEFAULT 3;"))
                    conn.commit()
                    print("[*] Schema upgrade: added 'max_concurrent_bookings_per_slot' column to 'website_settings'.")

        # 3. Check reviews.is_active
        if 'reviews' in table_names:
            columns = [c['name'] for c in inspector.get_columns('reviews')]
            if 'is_active' not in columns:
                with target_engine.connect() as conn:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN is_active BOOLEAN DEFAULT FALSE;"))
                    conn.commit()
                    print("[*] Schema upgrade: added 'is_active' column to 'reviews'.")
    except Exception as e:
        print(f"[!] Schema check notice: {e}")

def init_db(app_instance=None):
    """
    Safe, idempotent database initialization and migration.
    Creates schema tables, verifies columns, and seeds initial data.
    """
    target_app = app_instance or app
    with target_app.app_context():
        db.create_all()
        ensure_db_schema_upgrades()
        seed_database()

# Application instance factory invocation
app = create_app()

# Auto-initialize database schema and seeds on WSGI startup (e.g. Gunicorn on Render)
if not app.config.get('TESTING'):
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'services' not in tables or 'website_settings' not in tables:
                print("[*] WSGI startup: Initializing database tables and seed data...")
                init_db(app)
        except Exception as e:
            print(f"[!] Database startup initialization notice: {e}")

if __name__ == '__main__':
    with app.app_context():
        init_db(app)
    app.run(host='127.0.0.1', port=5000, debug=True)
