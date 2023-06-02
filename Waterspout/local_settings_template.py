import os

from .databases import DATABASES  # import DATABASES here so it gets pulled into the main app via the settings import

# Build paths inside the project like this: os.path.join(BASE_DIR, ...) - don't change
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
# this isn't a real key - make sure to CHANGE THIS to a cryptographically secure value
SECRET_KEY = 'change_me_to_something_real_please'

# Should the application use the Sentry logging service for errors? If so, set to True and provide the DSN
# for a valid Sentry account. Otherwise, leave as False
USE_SENTRY = False
SENTRY_DSN = 'ADD_SENTRY_DSN_HERE'

# The path where log files will be stored
LOG_FOLDER = os.path.join(BASE_DIR, "..", "logs")

# SECURITY WARNING: don't run with debug turned on in production!
# Generally speaking, you'll want to set this to False, but it's best to do it after you've confirmed
# a successful deployment because it can tell you useful messages while handling the deployment
DEBUG = True

# These must be set correctly in order to be able to access the admin interface
# See https://docs.djangoproject.com/en/4.2/ref/csrf/ for more on CSRF protection and
# https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-CSRF_TRUSTED_ORIGINS
# and https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-CSRF_COOKIE_DOMAIN
# for these specific settings
CSRF_COOKIE_DOMAIN = "openag.ucmerced.edu"
CSRF_TRUSTED_ORIGINS = ["https://openag.ucmerced.edu", "https://openag-dev.ucmerced.edu", "https://dap.ucmerced.edu"]

# You'll want to leave the SERVE_ADDRESS alone in most cases, except when you know that you need to change the port. If you
# change the port, make sure to adjust any reverse proxies/forwarders (ie, nginx or IIS) that access this application via
# WSGI or FastCGI.
# ALLOWED_HOSTS is a bit misleading - it's
# *really* referring to the allowed host*names* that someone can use to connect to this application. So make sure to
# expand the list with any IPs, domains, etc, that may be used to access the application in a browser
SERVE_ADDRESS = "*:8010"
ALLOWED_HOSTS = ["127.0.0.1", "localhost",]

# Need this for emails
# Which people should get emails when things go wrong?
# Format is like ADMINS = [("Nick", "nicksnotrealemailaddress@ucmerced.edu",), ("Someone Else", "someoneelse@ucmerced.edu",), ]
ADMINS = []

# AUTO_LOGIN handles the "user-less" system - the application won't be truly userless, but instead it will have *one* user
# that will be shared and automatically logged into when someone visits the web application.
# to enable it, set AUTO_LOGIN_ENABLED to True and set AUTO_LOGIN_USER to the username (in quotes) that all users will automatically share
# - make sure to create the auto login user first - after that, the web application won't prompt for logins anymore
AUTO_LOGIN_ENABLED = False
AUTO_LOGIN_USER = None

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# sets which fields get returned
LIMITED_RESULTS_FIELDS = ["region", "crop", "year", "xlandsc", "xwatersc", "water_per_acre", "net_revenue", "gross_revenue"]  # which fields should be available to access as results for download and via the API?

# POLLING not currently used
LONG_POLL_DURATION = 30  # when using HTTP long polls, how long should we leave the connection open for before returning?
POLL_CHECK_INTERVAL = 1  # how often should we poll the actual database for complete results during a long poll?

# EMAIL AND ALERTS
# Set the values for your SMTP server here to enable emails to be sent to the people
# specified in the ADMINS setting when errors occur
EMAIL_SUBJECT_PREFIX = '[Waterspout] '
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587  # the port email should be sent through
EMAIL_HOST_USER = ''  # username for email sending login
EMAIL_HOST_PASSWORD = ''  # the password for the account to send email through
EMAIL_USE_TLS = True  # specify whether to encrypt the traffic to the email server
SERVER_EMAIL = ''  # the email address to send alerts as

# How often should the run processor look for new model runs, in seconds?
# Shorter means that the effective time to model results is shorter, but causes
# more database and logging churn. Higher makes the time to model results a little
# longer, but reduces the amount of churn.
MODEL_RUN_CHECK_INTERVAL = 4

