# Generated by Django 3.1 on 2021-03-10 23:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0009_populate_priceyieldcorrection'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultset',
            name='in_calibration',
            field=models.BooleanField(default=True),
        ),
    ]