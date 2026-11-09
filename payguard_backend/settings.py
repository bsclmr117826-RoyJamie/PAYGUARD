# payguard_backend/settings.py
SECRET_KEY = 'django-insecure-payguard-fintech-sdlc-key'
DEBUG = False # Production hardened
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework',
    'payguard_backend',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'payguard_db',
        'USER': 'payguard_user',
        'PASSWORD': 'SecurePassword123!',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}