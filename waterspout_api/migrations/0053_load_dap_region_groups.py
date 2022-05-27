# Written by Nick

from django.db import migrations

from waterspout_api.load import dap


def load_water_agency_groups(apps, schema_editor):
    # get dap models by looking for the data folder
    ModelArea = apps.get_model('waterspout_api', 'ModelArea')

    # this is also important because on initial load of a new server, this should do nothing. There won't be data loaded
    # at the time this code runs, so no model areas should be caught. Instead, these groups will get created when DAP
    # model areas are loaded because this is also part of that code now
    dap_areas = ModelArea.objects.filter(data_folder="dap")
    for model_area in dap_areas:
        dap.load_water_agency_groups(model_area,
                                     RegionGroupSetModel=apps.get_model('waterspout_api', 'RegionGroupSet'),
                                     RegionGroupModel=apps.get_model('waterspout_api', 'RegionGroup'),
                                     RegionModel=apps.get_model('waterspout_api', 'Region')
                                     )


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0052_alter_regiongroupset_unique_together'),
    ]

    operations = [
        migrations.RunPython(load_water_agency_groups),
    ]
