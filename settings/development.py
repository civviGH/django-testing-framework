import os

from .common import *

DEBUG = True

ALLOWED_HOSTS = ['*']

DTF_ENABLE_WEBHOOKS = (os.environ.get("DTF_ENABLE_WEBHOOKS", "1") == "1")

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'main': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    'demo': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'demo-db.sqlite3'),
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

default_database = os.environ.get('DTF_DEFAULT_DATABASE', 'main')
DATABASES['default'] = DATABASES[default_database]
