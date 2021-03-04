# Generated by Django 3.1 on 2021-03-02 21:33 UTC
# Written by Nick that same day

import os
import csv

from django.db import migrations, models
from Waterspout.settings import BASE_DIR

def populate_price_yield_correction(apps, schema_editor):
    # load the calibration data as a CSV, then iterate through it and update the corresponding records in the DB

    # so, first, we need to look up all the calibration sets
    # and then check where their data came from

    # get the CalibrationSet object as the code/version existed at this point in the migration history
    # see https://docs.djangoproject.com/en/3.1/topics/migrations/
    CalibrationSet = apps.get_model('waterspout_api', "CalibrationSet")
    CalibratedParameter = apps.get_model('waterspout_api', "CalibratedParameter")

    existing_calibration_sets = CalibrationSet.objects.all()
    for calib_set in existing_calibration_sets:
        data_folder = calib_set.model_area.data_folder
        # we're only going to really have DAP right now, but this helps us check and make sure
        # we don't mess anything up if there's something else loaded first
        if data_folder == "dap":
            calibration_csv = os.path.join(BASE_DIR, "waterspout_api", "data", "dap", "dap_calibrated.csv")
        else:
            break

        with open(calibration_csv) as calib_data:
            calib_rows = csv.DictReader(calib_data)
            for row in calib_rows:
                # find the row that matches this calibration set, crop, and region
                # print(row["i"], " ", row["g"])
                #try:
                db_row = CalibratedParameter.objects.get(calibration_set=calib_set,
                                                         crop__crop_code=row["i"],
                                                         region__internal_id=row["g"],
                                                         )
                #except CalibratedParameter.DoesNotExist:
                #    pass

                # set its new value, and save it
                db_row.price_yield_correction_factor = row["price_yield_correction_param"]
                db_row.save()


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0008_auto_20210302_1333'),
    ]

    operations = [
        migrations.AddField(  # first we need to add the field to modelarea that specifies the folder to load from
            model_name='modelarea',
            name='data_folder',
            field=models.CharField(max_length=255, default="dap"),
        ),
        migrations.RunPython(populate_price_yield_correction)
    ]
