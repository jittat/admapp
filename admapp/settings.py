"""
Django settings for admapp project.

Generated by 'django-admin startproject' using Django 1.11.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '^f$7aqz2(qdz_sd*r8553vrbn8!qz@sbqed8sn)zxbnk($+fu7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'main.apps.MainConfig',
    'regis.apps.RegisConfig',
    'appl.apps.ApplConfig',
    'backoffice.apps.BackofficeConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'crispy_forms',
    'mailer',
    'supplements',
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

ROOT_URLCONF = 'admapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'admapp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'th'

TIME_ZONE = 'Asia/Bangkok'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

# Medias

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# EMAILS

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
MAILER_EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use these in production
# EMAIL_BACKEND = "mailer.backend.DbBackend"
# MAILER_EMAIL_BACKEND = 'django_ses.SESBackend'
#
# AWS_ACCESS_KEY_ID = 'YOUR-ACCESS-KEY-ID'
# AWS_SECRET_ACCESS_KEY = 'YOUR-SECRET-ACCESS-KEY'
# AWS_SES_REGION_NAME = 'us-west-2'
# AWS_SES_REGION_ENDPOINT = 'email.us-west-2.amazonaws.com'

# Crispy forms

CRISPY_TEMPLATE_PACK = 'bootstrap4'

# login/logout urls for backoffice

LOGOUT_REDIRECT_URL = 'backoffice:index'


# Admission App Configs

ADMISSION_TITLE = "โครงการรับสมัครนักเรียนเข้าศึกษาในมหาวิทยาลัยเกษตรศาสตร์ ปีการศึกษา 2561"
ADMISSION_SHORT_TITLE = "KU-TCAS'61"

VERIFY_NATIONAL_ID = True
FAKE_LOGIN = False
SUPER_ADMIN_APPLICANT_LOGIN_KEY = ''

BARCODE_DIR = '/tmp/'

ADM_EMAIL_FROM = 'admission@ku.ac.th'

ELIGIBILITY_CHECK = {
    'ช้างเผือก': 'white_elephant',
    'เรียนล่วงหน้า': 'advanced_placement',
}

# Manipulate Settings with Local Settings

try:
    from .settings_local import *
except ImportError:
    pass

# for django debug toolbar
if DEBUG:
    INTERNAL_IPS = ['127.0.0.1']
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

import sys
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'TEST_CHARSET': 'UTF8',
        'NAME': ':memory:',
    }
