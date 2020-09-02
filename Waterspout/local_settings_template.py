import os

from .databases import DATABASES  # import DATABASES here so it gets pulled into the main app via the settings import

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'change_me_to_something_real_please'  # this isn't a real key - make sure to CHANGE THIS

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SERVE_ADDRESS = "*:8010"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "192.168.1.21"]

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

LIMITED_RESULTS_FIELDS = ["region", "crop", "year", "xlandsc", "xwatersc"]  # which fields should be available to access as results for download and via the API?

LONG_POLL_DURATION = 30  # when using HTTP long polls, how long should we leave the connection open for before returning?
POLL_CHECK_INTERVAL = 1  # how often should we poll the actual database for complete results during a long poll?

# EMAIL AND ALERTS
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587  # the port email should be sent through
EMAIL_HOST_USER = ''  # username for email sending login
EMAIL_HOST_PASSWORD = ''  # the password for the account to send email through
EMAIL_USE_TLS = True  # specify whether to encrypt the traffic to the email server
SERVER_EMAIL = ''  # the email address to send alerts as

MODEL_RUN_CHECK_INTERVAL = 4
"""
    How often should the run processor look for new model runs, in seconds?
    Shorter means that the effective time to model results is shorter, but causes
    more database and logging churn. Higher makes the time to model results a little
    longer, but reduces the amount of churn.
"""
