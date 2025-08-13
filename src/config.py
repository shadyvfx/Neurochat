import os
from decouple import config

class Config:
    SECRET_KEY = config('SECRET_KEY', default='dev_key_change_this_in_production')
    # Fix database path to use absolute path to root instance directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL', default=f'sqlite:///{os.path.join(INSTANCE_DIR, "users.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = config('WTF_CSRF_ENABLED', default=True, cast=bool)

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SECRET_KEY = config('SECRET_KEY')  # Must be set in production
    
class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config_dict = {
    'production': ProductionConfig,
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
