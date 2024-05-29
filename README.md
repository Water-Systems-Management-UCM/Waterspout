# Waterspout
Waterspout is a server-side system for managing, running, and viewing agricultural optimization models. It
exposes an API and user management system for the model and manages model runs on the back end.

Waterspout is a Django application, so the folder structure follows Django Model-View-Template patterns,
though we do not use Django's templating engine. 

## Deployment
Deployment code and process are currently private

## Developing with Waterspout
First, you'll need a copy of the Dapper repository installed - contact Nick about that since it's currently private.

Then, to install this repository, clone it, create a virtual environment or conda environment, then
go to the repository root, activate your conda environment, and run:

```
del db.sqlite3
python -m pip install -r requirements.txt
python manage.py migrate && python manage.py load_initial_data --area agwa && python manage.py createsuperuser && python manage.py add_user_to_org --user=yourusername --organization=WA && python manage.py update_feature_packages
```

replacing "yourusername" in the final command with the name of the user you plan to create in the createsuperuser step.

From there, whenever you need to run a normal update, just pull changes from the repository and run:
```
python -m pip install -r requirements.txt
python manage.py migrate
```

## License
Waterspout is currently copyright-protected by the Regents of the University of California, but may move
to an OSI-approved open source license at some point in the future.