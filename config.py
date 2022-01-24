# config.py

"""
This file contains the configurations for different environments
"""

import os
import json

# Here, we obtain environment variables directly from computer
# Useful for running in a terminal

SERVER_NAME = os.environ.get("SERVER_NAME")


class Config(object):
    # Put any configurations common across all environments
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 'sqlite:///database.db'
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = "session"
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SERVER_NAME = SERVER_NAME if SERVER_NAME else None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = SECRET_KEY or "my-secret-key"
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    # Defines the complexity of the hashing algorithm
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS') or '13') or 13
    # Define path for upload folder
    UPLOAD_FOLDER = "app/static/uploads"
    # PyOTP Key
    OTP_BASE32_SECRET = os.environ.get("OTP_BASE32_SECRET") or 'otp-base32-secret'
    # Redis configurations
    REDIS_HOST = os.environ.get("REDIS_HOST") or 'localhost'
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD") or ''
    REDIS_URL = os.environ.get("REDIS_URL") or 'redis://'
    REDIS_PORT = int(os.environ.get("REDIS_PORT", '6379') or 6379)
    REDIS_ROOT = os.environ.get("REDIS_ROOT") or 'cloudwalk'
    # Define path for logs folder
    LOG_FOLDER = "app/logs"
    # used for email and phone confirmation
    EMAIL_CONFIRMATION_KEY = os.environ.get("EMAIL_CONFIRMATION_KEY") or 'email-confirm-key'
    PHONE_CONFIRMATION_KEY = os.environ.get("PHONE_CONFIRMATION_KEY") or 'phone-confirm-key'
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT") or 'security-password-salt'
    # use for password reset
    RESET_PASSWORD_KEY = os.environ.get("RESET_PASSWORD_KEY") or 'reset-password-key'
    # email server details to configure Flask to send email immediately after an error, with stack trace in email body
    MAIL_SERVER = os.environ.get("MAIL_SERVER")  # if not set, then emailing errors will be disabled
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)  # set to standard port 25 if not set
    # Transport Layer Security(TLS) with SMTP provides confidentiality and authentication for email traffic
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") or 1
    # mail server credentials, optional
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    # list of the email addresses that will receive error reports
    ADMINS = json.loads(os.environ.get("ADMINS", "[]") or '[]') or []
    # Default administrator details
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'administrator')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', None)
    ADMIN_LASTNAME = os.environ.get('ADMIN_LASTNAME', 'Last')
    ADMIN_FIRSTNAME = os.environ.get('ADMIN_FIRSTNAME', 'First')
    ADMIN_PHONE_NUMBER = os.environ.get('ADMIN_PHONE_NUMBER', '')
    ADMIN_EMAIL_ADDRESS = os.environ.get('ADMIN_EMAIL_ADDRESS', '')
    # Set flag for if server is hosted on Python Anywhere
    IS_PYTHON_ANYWHERE = os.environ.get("IS_PYTHON_ANYWHERE") is not None
    # For email address validation
    REAL_EMAIL_API_KEY = os.environ.get("REAL_EMAIL_API_KEY")
    # Indicates whether to log to stdout or to a file
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')


class DevelopmentConfig(Config):
    """Development configurations"""
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 4  # to save on development time, let's reduce this
    SQLALCHEMY_ECHO = False  # allows SQLAlchemy to log errors
    SQLALCHEMY_TRACK_MODIFICATIONS = True  # allows SQLAlchemy to track changes while running


class ProductionConfig(Config):
    """Production configurations"""
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestingConfig(DevelopmentConfig):
    """Testing configurations"""
    TESTING = True
    # Give a testing database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_database.db'
    SQLALCHEMY_ECHO = False


app_config = {
    'development': 'DevelopmentConfig',
    'production': 'ProductionConfig',
    'testing': 'TestingConfig',
}
