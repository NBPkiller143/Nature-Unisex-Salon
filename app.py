import os
import time
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from config import config
from models import db, User, Service, Appointment, Gallery, Review, ContactEnquiry, WebsiteSetting
from utils import (
    save_uploaded_image, 
    build_whatsapp_booking_url, 
    build_whatsapp_general_url, 
    build_whatsapp_enquiry_url, 
    clean_phone_number,
    sanitize_text,
    sanitize_email
)
from seed_data import seed_database

# In-memory rate limiting tracking
login_failed_attempts = defaultdict(list)

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        
    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))
    
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
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # HTTP Security Headers Middleware (OWASP Top 10 Hardening)
    @app.after_request
    def apply_security_headers(response):
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
    
    # Template filters for formatting phone and WhatsApp links
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
        
        return {
            'settings': settings,
            'nav_services': nav_services,
            'current_year': datetime.now().year,
            'whatsapp_chat_url': whatsapp_url,
            'salon_clean_phone': clean_salon_phone
        }



    # ==========================================
    # PUBLIC ROUTES
    # ==========================================
    
    @app.route('/')
    def index():
        """Home page with hero, featured services, gallery highlights, and customer reviews."""
        featured_services = Service.query.filter_by(is_active=True).order_by(Service.display_order.asc()).limit(6).all()
        gallery_items = Gallery.query.filter_by(is_active=True).order_by(Gallery.created_at.desc()).limit(6).all()
        reviews = Review.query.filter_by(is_active=True).order_by(Review.display_order.asc(), Review.created_at.desc()).limit(6).all()
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
            
        services_list = query.order_by(Service.gender_target.asc(), Service.display_order.asc()).all()
        all_services = Service.query.filter_by(is_active=True).all()
        categories = sorted(list(set(s.category for s in all_services)))
        
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
        """Customer testimonials & review submission."""
        if request.method == 'POST':
            name = sanitize_text(request.form.get('customer_name', ''), max_length=80)
            rating_val = request.form.get('rating', '5')
            try:
                rating = int(rating_val)
            except ValueError:
                rating = 5
            review_text = sanitize_text(request.form.get('review_text', ''), max_length=1500)
            service_name = sanitize_text(request.form.get('service_name', ''), max_length=100)
            
            if not name or not review_text:
                flash('Please provide your name and review details.', 'error')
                return redirect(url_for('reviews'))
                
            new_review = Review(
                customer_name=name,
                rating=min(max(rating, 1), 5),
                review_text=review_text,
                service_name=service_name,
                is_active=True
            )
            db.session.add(new_review)
            db.session.commit()
            flash('Thank you for sharing your experience! Your review has been submitted.', 'success')
            return redirect(url_for('reviews'))
            
        reviews_list = Review.query.filter_by(is_active=True).order_by(Review.created_at.desc()).all()
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
        data = request.get_json() or request.form
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
        """Appointment booking page."""
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
            
            # Validation
            if not name or not phone or not app_date or not app_time:
                flash('Please complete all required fields (Name, Phone, Date, and Time).', 'error')
                return redirect(url_for('booking', service_id=service_id))
                
            if service_id:
                svc_obj = db.session.get(Service, service_id)
                if svc_obj:
                    service_name = svc_obj.name
            if not service_name:
                service_name = "General Salon Consultation"
                
            appointment = Appointment(
                customer_name=name,
                phone=phone,
                email=email,
                gender=gender,
                service_id=service_id,
                service_name=service_name,
                appointment_date=app_date,
                appointment_time=app_time,
                message=notes,
                status='Pending'
            )
            db.session.add(appointment)
            db.session.commit()
            
            # Build WhatsApp redirect URL
            whatsapp_url = build_whatsapp_booking_url(
                whatsapp_number=settings.whatsapp_number,
                customer_name=name,
                service_name=service_name,
                appointment_date=app_date,
                appointment_time=app_time,
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

    # API Endpoints for Ajax Booking and Inquiries
    @app.route('/api/book', methods=['POST'])
    def api_book():
        """AJAX endpoint for instant booking."""
        data = request.get_json() or request.form
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
            
        if service_id:
            try:
                svc_obj = db.session.get(Service, int(service_id))
                if svc_obj:
                    service_name = svc_obj.name
            except Exception:
                pass
        if not service_name:
            service_name = "General Consultation"
            
        appointment = Appointment(
            customer_name=name,
            phone=phone,
            email=email,
            gender=gender,
            service_id=int(service_id) if service_id else None,
            service_name=service_name,
            appointment_date=app_date,
            appointment_time=app_time,
            message=notes,
            status='Pending'
        )
        db.session.add(appointment)
        db.session.commit()
        
        settings = WebsiteSetting.get_settings()
        whatsapp_url = build_whatsapp_booking_url(
            whatsapp_number=settings.whatsapp_number,
            customer_name=name,
            service_name=service_name,
            appointment_date=app_date,
            appointment_time=app_time,
            notes=notes
        )
        
        return jsonify({
            'success': True,
            'message': 'Thank you! Your appointment request has been received. Nature Unisex Salon will contact you shortly to confirm your booking.',
            'appointment_id': appointment.id,
            'whatsapp_url': whatsapp_url
        })

    # ==========================================
    # ADMIN ROUTES
    # ==========================================

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Admin authentication login with brute-force protection and open-redirect defense."""
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
        """Admin sign out."""
        logout_user()
        flash('You have been signed out safely.', 'info')
        return redirect(url_for('admin_login'))


    @app.route('/admin')
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
        return render_template(
            'admin/appointments.html',
            appointments=appointments,
            active_status=status_filter,
            search_query=search_query
        )

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
        """Manage customer testimonials."""
        reviews = Review.query.order_by(Review.created_at.desc()).all()
        return render_template('admin/reviews.html', reviews=reviews)

    @app.route('/admin/reviews/add', methods=['POST'])
    @login_required
    def admin_add_review():
        """Add new review manually."""
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
        flash('Review added successfully.', 'success')
        return redirect(url_for('admin_reviews'))

    @app.route('/admin/reviews/toggle/<int:review_id>', methods=['POST'])
    @login_required
    def admin_toggle_review(review_id):
        """Toggle review visibility."""
        review = db.session.get(Review, review_id)
        if review:
            review.is_active = not review.is_active
            db.session.commit()
            flash('Review status updated.', 'info')
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
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('404.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('404.html'), 429

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500


    return app

# Create application instance
app = create_app()

# Auto-initialize and seed DB when running directly or in staging/prod
with app.app_context():
    db.create_all()
    seed_database()

if __name__ == '__main__':
    # Local run
    app.run(host='127.0.0.1', port=5000, debug=True)
