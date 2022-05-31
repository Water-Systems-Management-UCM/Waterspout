# Written by Nick

from django.db import migrations, models
import django.db.models.deletion

from waterspout_api.load import dap


def load_multipliers(apps, schema_editor):
    # get dap models by looking for the data folder
    ModelArea = apps.get_model('waterspout_api', 'ModelArea')

    # this is also important because on initial load of a new server, this should do nothing. There won't be data loaded
    # at the time this code runs, so no model areas should be caught. Instead, these groups will get created when DAP
    # model areas are loaded because this is also part of that code now
    dap_areas = ModelArea.objects.filter(data_folder="dap")
    for model_area in dap_areas:
        dap.load_multipliers(model_area,
                         RegionModel=apps.get_model('waterspout_api', 'Region'),
                         CropModel=apps.get_model('waterspout_api', 'Crop'),
                         MultipliersModel=apps.get_model('waterspout_api', 'EmploymentMultipliers'),
                        )


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0054_rename_multipliers_20220531_1112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employmentmultipliers',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='multipliers',
                                    to='waterspout_api.region'),
        ),
        migrations.RunPython(load_multipliers),
    ]
