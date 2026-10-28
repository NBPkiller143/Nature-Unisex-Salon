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
        """Verify mandatory production configurations at startup."""
        secret = os.environ.get('SECRET_KEY')
        if not secret or secret == 'nature-unisex-salon-super-secret-key-2026-secure':
            raise ValueError(
                "CRITICAL: A secure random SECRET_KEY environment variable is mandatory in production. "
                "Configure SECRET_KEY in your Render environment settings."
            )
        
        db_url = os.environ.get('DATABASE_URL')
        allow_sqlite = os.environ.get('ALLOW_SQLITE_IN_PRODUCTION', 'false').lower() in ('true', '1')
        if not db_url and not allow_sqlite:
            raise RuntimeError(
                "CRITICAL: DATABASE_URL is not set in production. "
                "Render instances have ephemeral filesystems; running SQLite without a persistent disk "
                "will cause customer bookings and data to be lost upon restart. "
                "Provision a PostgreSQL database and provide DATABASE_URL, or explicitly set "
                "ALLOW_SQLITE_IN_PRODUCTION=true if using an attached persistent Render Disk."
            )

    # In production, require SECRET_KEY from env or raise error when accessed
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
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
        # Fallback only if explicitly allowed via ALLOW_SQLITE_IN_PRODUCTION
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'instance' / 'salon.db'}"

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
