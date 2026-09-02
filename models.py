from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def get_utc_now():
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    """Admin User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Service(db.Model):
    """Salon Service model with pricing, categories, and gender targets."""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    gender_target = db.Column(db.String(20), default='Unisex', nullable=False) # 'Men', 'Women', 'Unisex'
    category = db.Column(db.String(50), nullable=False, index=True) # 'Hair', 'Skin', 'Grooming', 'Makeup', 'Spa', 'Bridal', 'Packages'
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    duration_mins = db.Column(db.Integer, default=30)
    image_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    
    # Relationship with appointments
    appointments = db.relationship('Appointment', backref='service_ref', lazy='dynamic')
    
    def formatted_price(self, currency="₹"):
        if self.price == int(self.price):
            return f"{currency}{int(self.price)}"
        return f"{currency}{self.price:,.2f}"

    def formatted_duration(self):
        if not self.duration_mins:
            return "30 mins"
        if self.duration_mins >= 60:
            hrs = self.duration_mins // 60
            mins = self.duration_mins % 60
            if mins == 0:
                return f"{hrs} hr" if hrs == 1 else f"{hrs} hrs"
            return f"{hrs} hr {mins} mins"
        return f"{self.duration_mins} mins"

    def __repr__(self):
        return f'<Service {self.name} - {self.category} ({self.gender_target})>'


class Appointment(db.Model):
    """Customer appointment booking request."""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(25), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=True)
    gender = db.Column(db.String(20), default='Not Specified')
    
    # Service association (foreign key optional with fallback name string for flexibility)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='SET NULL'), nullable=True)
    service_name = db.Column(db.String(120), nullable=False)
    
    appointment_date = db.Column(db.String(20), nullable=False, index=True) # YYYY-MM-DD format
    appointment_time = db.Column(db.String(20), nullable=False) # e.g. "11:00 AM"
    message = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(20), default='Pending', index=True) # 'Pending', 'Confirmed', 'Completed', 'Cancelled'
    admin_notes = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=get_utc_now, index=True)
    
    def __repr__(self):
        return f'<Appointment {self.id} - {self.customer_name} ({self.status})>'


class Gallery(db.Model):
    """Salon portfolio and media items."""
    __tablename__ = 'gallery'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Hair', index=True) # 'Hair', 'Makeup', 'Bridal', 'Grooming', 'Interior', 'Transformations'
    image_url = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    
    def __repr__(self):
        return f'<Gallery {self.title} ({self.category})>'


class Review(db.Model):
    """Customer Testimonials and Reviews."""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, default=5, nullable=False) # 1-5
    review_text = db.Column(db.Text, nullable=False)
    service_name = db.Column(db.String(100), nullable=True) # e.g. 'Hydra Facial & Beard Sculpting'
    is_active = db.Column(db.Boolean, default=True, index=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    
    def __repr__(self):
        return f'<Review {self.customer_name} ({self.rating}★)>'


class ContactEnquiry(db.Model):
    """Customer inquiries submitted via the Contact form."""
    __tablename__ = 'contact_enquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    subject = db.Column(db.String(150), default='General Salon Inquiry')
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=get_utc_now, index=True)
    
    def __repr__(self):
        return f'<ContactEnquiry {self.id} from {self.name}>'


class WebsiteSetting(db.Model):
    """Global configuration settings for the salon."""
    __tablename__ = 'website_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    salon_name = db.Column(db.String(120), default='Nature Unisex Salon')
    tagline = db.Column(db.String(200), default='Style. Care. Confidence.')
    phone = db.Column(db.String(50), default='+91 74837 37517')
    whatsapp_number = db.Column(db.String(30), default='917483737517')
    email = db.Column(db.String(120), default='info@natureunisexsalon.com')
    address = db.Column(db.String(255), default='Kashi Vishwanatha, 12, Anjaneya Temple Street, Vannarpet, Yerappa Garden, Austin Town, Neelasandra, Bengaluru, Karnataka 560047, India')
    google_maps_url = db.Column(db.String(500), default='https://www.google.com/maps/place/Nature+unisex+salon/@12.9570761,77.6192442,15z/data=!4m6!3m5!1s0x3bae156290e25a91:0x923594a7d37cb230!8m2!3d12.9565087!4d77.6196044!16s%2Fg%2F11z1zkml55?entry=ttu')
    google_maps_embed = db.Column(db.Text, default='https://maps.google.com/maps?q=12.9565087,77.6196044+(Nature%20Unisex%20Salon)&t=&z=16&ie=UTF8&iwloc=B&output=embed')
    instagram_url = db.Column(db.String(255), default='https://www.instagram.com/nature_unisex_salon72/')
    facebook_url = db.Column(db.String(255), default='')
    opening_hours_weekdays = db.Column(db.String(100), default='Sunday - Monday: 09:00 - 21:00')
    opening_hours_weekends = db.Column(db.String(100), default='Everyday: 09:00 - 21:00 (Open All 7 Days)')
    hero_headline = db.Column(db.String(200), default='Style. Care. Confidence.')
    hero_subtext = db.Column(db.Text, default='Experience premium hair styling, skin care, grooming, and rejuvenating beauty treatments crafted for both men and women in an elegant, hygienic haven.')
    about_text = db.Column(db.Text, default='Nature Unisex Salon is a contemporary sanctuary dedicated to helping men and women embrace their finest personal style. We blend botanical care with state-of-the-art styling techniques to deliver an unhurried, luxurious grooming experience.')
    currency_symbol = db.Column(db.String(10), default='₹')
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    @classmethod
    def get_settings(cls):
        """Fetch the current settings instance, or create a default one if none exists."""
        setting = cls.query.first()
        if not setting:
            setting = cls()
            db.session.add(setting)
            db.session.commit()
        return setting
    
    def __repr__(self):
        return f'<WebsiteSetting {self.salon_name}>'
