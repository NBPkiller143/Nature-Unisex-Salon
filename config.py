import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nature-unisex-salon-super-secret-key-2026-secure'
    
    # Database Configuration:
    # Uses SQLite by default for local development.
    # When deployed to Render/Heroku/AWS, DATABASE_URL will be used.
    # Fix postgres:// URI prefix for SQLAlchemy 1.4+ compatibility
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = db_url or f"sqlite:///{basedir / 'instance' / 'salon.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings
    UPLOAD_FOLDER = basedir / 'static' / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # Business Defaults (can be overridden via Admin Settings in DB)
    SALON_NAME = os.environ.get('SALON_NAME', 'Nature Unisex Salon')
    SALON_PHONE = os.environ.get('SALON_PHONE', '+91 74837 37517')
    SALON_WHATSAPP = os.environ.get('SALON_WHATSAPP', '917483737517')
    SALON_EMAIL = os.environ.get('SALON_EMAIL', 'info@natureunisexsalon.com')
    SALON_ADDRESS = os.environ.get('SALON_ADDRESS', 'Nature Unisex Salon, Austin Town / Neelasandra, Bengaluru, Karnataka 560047, India')

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
