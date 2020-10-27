"""
Django settings for Waterspout project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import re

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from Waterspout.local_settings import *

# sentry config - only run if DEBUG is False (basically, in production)
if not DEBUG:
    sentry_sdk.init(
        dsn="https://a39545e9b4c940c18e62629856dedaed@o462396.ingest.sentry.io/5465746",
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )

# With DRF, I don't see a way to use the Django `url` include in templates. So, I'd like to
# have a single place to define API URLs that we can include in templates. That's here.
API_BASE_URL = "/api/"
API_URLS = {  # partial is used in URLconf, full is used in templates
    "regions": {"partial": "regions", "full": f"{API_BASE_URL}regions/"},
    "crops": {"partial": "crops", "full": f"{API_BASE_URL}crops/"},
    "model_runs": {"partial": "model_runs", "full": f"{API_BASE_URL}model_runs/"},
    "region_modifications": {"partial": "region_modifications", "full": f"{API_BASE_URL}region_modifications/"},
    "users": {"partial": "users", "full": f"{API_BASE_URL}users/"},
}


# We want Django to ignore some 404s because they're mostly just attempts by bots
# to drive-by exploit. I don't want a notification for every single one.
IGNORABLE_404_URLS = [
    re.compile(r'\.(php|cgi|sql|pl)$'),
    re.compile(r'^/phpmyadmin/'),
    re.compile(r'^/hudson'),
    re.compile(r'^/requested.html'),
    re.compile(r'^/ab2g'),
    re.compile(r'^/ab2h'),
    re.compile(r'^/.env'),
    re.compile(r'^/boaform'),
]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
	'DEFAULT_AUTHENTICATION_CLASSES': (
		'rest_framework.authentication.TokenAuthentication',
		'rest_framework.authentication.BasicAuthentication',
		'rest_framework.authentication.SessionAuthentication',
	),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 1000,
}

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'waterspout_api.apps.WaterspoutApiConfig',
    'rest_framework',
    'rest_framework.authtoken',
    'guardian',  # gives us object-level permissions
]

MIDDLEWARE = [
    'django.middleware.common.BrokenLinkEmailsMiddleware',  # we don't really need broken link notifications, but this way, we stop getting them as errors
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # default
    'guardian.backends.ObjectPermissionBackend',
)

ROOT_URLCONF = 'Waterspout.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'waterspout_api.context_processors.api_urls',
            ],
        },
    },
]

WSGI_APPLICATION = 'Waterspout.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

if DEBUG:  # if DEBUG is on, don't email admins when problems happen
    log_handlers = ['console', 'file_debug']
else:
    log_handlers = ['console', 'file_debug', 'file_error', 'email_error', 'email_warn']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s : %(asctime)s : %(module)s : %(process)d : %(thread)d : %(message)s'
        },
        'simple': {
            'format': '%(levelname)s:%(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO' if not DEBUG else 'DEBUG',
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log') if DEBUG else os.path.join(BASE_DIR, "..", "logs", "waterspout_debug.log"),
            'formatter': 'verbose'
        },
        'file_error': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'warnings.log') if DEBUG else os.path.join(BASE_DIR, "..", "logs",
                                                                                       "waterspout_error.log"),
            'formatter': 'verbose'
        },
        'file_model_run_processor': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'waterspout_process_runs.log') if DEBUG else os.path.join(BASE_DIR, "..", "logs",
                                                                                          "waterspout_process_runs.log"),
            'formatter': 'verbose'
        },
        'email_warn': {
            'level': "WARNING",
            'class': "django.utils.log.AdminEmailHandler",
        },
        'email_error': {
            'level': "ERROR",
            'class': "django.utils.log.AdminEmailHandler"
        },
    },
    'loggers': {
        'django': {
            'handlers': log_handlers,
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'Dapper': {
            'handlers': log_handlers,
            'level': 'DEBUG'
        },
        'waterspout_service_run_processor': {
            'handlers': ['file_model_run_processor', 'email_warn', 'email_error'],
            'level': 'DEBUG'
        },

        'waterspout': {
            'handlers': log_handlers,
            'level': 'DEBUG'
        },

        'waterspout_api': {
            'handlers': log_handlers,
            'level': 'DEBUG'
        },

        'Waterspout': {
            'handlers': log_handlers,
            'level': 'DEBUG'
        },
    },
}