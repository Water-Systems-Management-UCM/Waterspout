# Waterspout
Waterspout is a server-side system for managing, running, and viewing agricultural optimization models.

## Developing with Waterspout
First, you'll need a copy of the Dapper repository installed - contact Nick about that since it's currently private.

Then, to install this repository, clone it, create a virtual environment or conda environment, then
go to the repository root, activate your conda environment, and run:

```
del db.sqlite3
python -m pip install -r requirements.txt
python manage.py migrate && python manage.py load_initial_data --region dap && python manage.py createsuperuser && python manage.py add_user_to_org --user=yourusername --organization=DAP
```

replacing "yourusername" in the final command with the name of the user you plan to create in the createsuperuser step.

From there, whenever you need to run a normal update, just pull changes from the repository and run:
```
python -m pip install -r requirements.txt
python manage.py migrate
```