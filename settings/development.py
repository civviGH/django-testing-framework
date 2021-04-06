import os

from .common import *

DEBUG = True

ALLOWED_HOSTS = ['*']

DTF_ENABLE_WEBHOOKS = (os.environ.get("DTF_ENABLE_WEBHOOKS", "1") == "1")

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
