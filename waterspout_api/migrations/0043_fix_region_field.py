from django.db import migrations, models

"""
    I think ultimately this isn't necessary, but just in case Django applies it to a DBMS. The original migration
    had the wrong default value. Django set those values into the existing records (which needed manual intervention),
    but now we want to make sure the correct default is stored in the DBMS if needed. It is corrected in the models.
"""
class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0042_change_modeled_type_to_macro'),
    ]

    operations = [
        migrations.AlterField(
            model_name='region',
            name='default_behavior',
            field=models.SmallIntegerField(choices=[(1, 'Modeled'), (2, 'Removed'), (3, 'Fixed')], default=0),
        ),
    ]
