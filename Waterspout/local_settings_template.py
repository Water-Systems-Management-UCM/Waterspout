import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'change_me_to_something_real_please'  # this isn't a real key - make sure to CHANGE THIS

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

LONG_POLL_DURATION = 30  # when using HTTP long polls, how long should we leave the connection open for before returning?
POLL_CHECK_INTERVAL = 1  # how often should we poll the actual database for complete results during a long poll?

# EMAIL AND ALERTS
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587  # the port email should be sent through
EMAIL_HOST_USER = ''  # username for email sending login
EMAIL_HOST_PASSWORD = ''  # the password for the account to send email through
EMAIL_USE_TLS = True  # specify whether to encrypt the traffic to the email server
SERVER_EMAIL = ''  # the email address to send alerts as

DB_HOST = "127.0.0.1"
DB_PORT = 5432
DB_SCHEMA = "agmodels"
DB_NAME = "waterspout"
DB_USER = "mydatabaseuser"
DB_PASSWORD = "mydbpassword"

PG_DATABASES = {  # We define this like this so Ansible can destroy the first database block and then just rename this in the config
	'default': {  # these database settings assume you're connecting to a Postgres database. If you'll use something else, consult the Django documentation
		'ENGINE': 'django.db.backends.postgresql',  # this is for Postgres - if you'll use something else like MySQL, consult Django documentation
		'HOST': DB_HOST,  # the IP address or publicly accessible base URL of the database. If you're running the database server on the same computer as the web server, this value is correct already
		'PORT': DB_PORT,  # the port the database runs on. This value is the default for Postgres
		'NAME': DB_NAME,  # no need to change, defined above
		'USER': DB_USER,  # replace with the username for your database
		'PASSWORD': DB_PASSWORD,  # replace with the password for your database
		'OPTIONS': {  # you don't need to modify this line or the next one *if* you're using PostgreSQL
			'options': '-c search_path={}'.format(DB_SCHEMA)
		},
	}
}

MODEL_RUN_CHECK_INTERVAL = 4
"""
    How often should the run processor look for new model runs, in seconds?
    Shorter means that the effective time to model results is shorter, but causes
    more database and logging churn. Higher makes the time to model results a little
    longer, but reduces the amount of churn.
"""
