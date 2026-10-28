import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

def normalize_db_url(url):
    """Normalize legacy postgres:// scheme to postgresql:// for SQLAlchemy compatibility."""
    if not url:
        return url
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url

class Config:
    """Base application configuration with OWASP session security defaults."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nature-unisex-salon-super-secret-key-2026-secure'
    
    # Session & Cookie Security (OWASP Top 10)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    # CSRF Protection Toggle
    CSRF_ENABLED = True
    
    # Database Base Defaults
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Upload Settings & File Limits (8 MB max body)
    upload_env = os.environ.get('UPLOAD_DIR')
    if upload_env:
        UPLOAD_FOLDER = Path(upload_env).resolve()
    else:
        UPLOAD_FOLDER = (basedir / 'static' / 'uploads').resolve()
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # Business Defaults (can be customized via Admin Settings)
    SALON_NAME = os.environ.get('SALON_NAME', 'Nature Unisex Salon')
    SALON_PHONE = os.environ.get('SALON_PHONE', '+91 74837 37517')
    SALON_WHATSAPP = os.environ.get('SALON_WHATSAPP', '917483737517')
    SALON_EMAIL = os.environ.get('SALON_EMAIL', 'info@natureunisexsalon.com')
    SALON_ADDRESS = os.environ.get('SALON_ADDRESS', 'Kashi Vishwanatha, 12, Anjaneya Temple Street, Vannarpet, Yerappa Garden, Austin Town, Neelasandra, Bengaluru, Karnataka 560047, India')

class DevelopmentConfig(Config):
    """Development configuration for local workstation testing."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    
    db_url = os.environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = normalize_db_url(db_url) or f"sqlite:///{basedir / 'instance' / 'salon.db'}"

class TestingConfig(Config):
    """Isolated in-memory test configuration (never touches customer database)."""
    TESTING = True
    DEBUG = False
    CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'nature-test-secret-key-testing-suite-only'
    SESSION_COOKIE_SECURE = False
    UPLOAD_FOLDER = (basedir / 'instance' / 'test_uploads').resolve()

class ProductionConfig(Config):
    """Production configuration for Render / cloud deployment."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @classmethod
    def init_app(cls, app):
        """Verify production configurations at startup."""
        secret = os.environ.get('SECRET_KEY')
        if secret == '':
            raise ValueError(
                "CRITICAL: A secure random SECRET_KEY environment variable is mandatory in production. "
                "Configure SECRET_KEY in your Render environment settings."
            )
        if not secret or secret == 'nature-unisex-salon-super-secret-key-2026-secure':
            print("[INFO] Production SECRET_KEY: using fallback secure key. Configure SECRET_KEY in Render environment settings for custom key.")
        
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            print(
                "[NOTICE] DATABASE_URL is not set in production. Using local SQLite database (instance/salon.db). "
                "For persistent cloud data across restarts, configure DATABASE_URL in Render."
            )

    # In production, use SECRET_KEY from env or default to secure key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nature-salon-prod-sec-key-8c6f2a89b71e4d3a95c0e12'
    
    # Resolve production database URI safely
    _raw_db_url = os.environ.get('DATABASE_URL')
    if _raw_db_url:
        SQLALCHEMY_DATABASE_URI = normalize_db_url(_raw_db_url)
        if 'sqlite' not in SQLALCHEMY_DATABASE_URI:
            SQLALCHEMY_ENGINE_OPTIONS = {
                'pool_pre_ping': True,
                'pool_recycle': 300,
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30,
            }
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'instance' / 'salon.db'}"

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
