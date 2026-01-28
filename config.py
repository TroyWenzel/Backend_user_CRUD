import os

class DevelopmentConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-development'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300
    
class TestingConfig:
    SECRET_KEY = 'test-secret-key-for-testing'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Render provides DATABASE_URL, not SQLALCHEMY_DATABASE_URI
    DATABASE_URL = os.environ.get('DATABASE_URL')

    # SQLAlchemy doesn't accept postgres://, needs postgresql://
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///production.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300