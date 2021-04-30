# Generated by Django 3.2 on 2021-04-28 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0025_auto_20210428_1320'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelarea',
            name='max_rainfall',
            field=models.PositiveSmallIntegerField(default=200),
        ),
        migrations.AddField(
            model_name='modelarea',
            name='min_rainfall',
            field=models.PositiveSmallIntegerField(default=10),
        ),
    ]