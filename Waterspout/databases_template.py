import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

SQLITE_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

DATABASES = SQLITE_DATABASES