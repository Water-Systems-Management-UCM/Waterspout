# Generated by Django 3.1 on 2020-10-07 20:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0003_helpdocument'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cropmodification',
            name='crop_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='modifications', to='waterspout_api.cropgroup'),
        ),
        migrations.AlterField(
            model_name='cropmodification',
            name='max_land_area_proportion',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='cropmodification',
            name='min_land_area_proportion',
            field=models.FloatField(blank=True, null=True),
        ),
    ]