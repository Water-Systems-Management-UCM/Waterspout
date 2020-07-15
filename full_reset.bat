REM This is just for local development use, but resets the environment for local development use and installs dependencies, etc
del db.sqlite3
python -m pip install -r requirements.txt
python manage.py makemigrations && python manage.py migrate && python manage.py load_initial_data && python manage.py createsuperuser
python manage.py add_user_to_org --user=dsx --organization=DAP