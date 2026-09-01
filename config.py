import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

from datetime import timedelta

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nature-unisex-salon-super-secret-key-2026-secure'
    
    # Session & Cookie Security (OWASP Standard)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True automatically in Production / HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    # Database Configuration:
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = db_url or f"sqlite:///{basedir / 'instance' / 'salon.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings & Request Body Limit (Prevents memory flood DoS)
    UPLOAD_FOLDER = basedir / 'static' / 'uploads'
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

    
    # Business Defaults (can be overridden via Admin Settings in DB)
    SALON_NAME = os.environ.get('SALON_NAME', 'Nature Unisex Salon')
    SALON_PHONE = os.environ.get('SALON_PHONE', '+91 74837 37517')
    SALON_WHATSAPP = os.environ.get('SALON_WHATSAPP', '917483737517')
    SALON_EMAIL = os.environ.get('SALON_EMAIL', 'info@natureunisexsalon.com')
    SALON_ADDRESS = os.environ.get('SALON_ADDRESS', 'Kashi Vishwanatha, 12, Anjaneya Temple Street, Vannarpet, Yerappa Garden, Austin Town, Neelasandra, Bengaluru, Karnataka 560047, India')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Ensure production uses strong secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-nature-salon-secure-fallback-key'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
