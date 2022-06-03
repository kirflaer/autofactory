import enum
import os
from pathlib import Path
from dotenv import load_dotenv
from environ import Env

env = Env()
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'catalogs',
    'api',
    'factory_core',
    'packing',
    'users',
    'rest_framework',
    'django_filters',
    'tests',
    'tasks',
    'warehouse_management'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'autofactory_head.urls'
AUTH_USER_MODEL = "users.User"
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
ADDITIONAL_BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_ADDITIONAL_DIR = os.path.join(ADDITIONAL_BASE_DIR, "templates")
CATALOGS_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, "catalogs")
OPERATIONS_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, "operation")
SERVICES_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, "service")
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR, CATALOGS_TEMPLATES_DIR,
                 TEMPLATES_ADDITIONAL_DIR, OPERATIONS_TEMPLATES_DIR,
                 SERVICES_TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'autofactory_head.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'api.permissions.IsActivatedDevice',
    ],
}

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "index"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
VERSION = '1.1.3.0'
