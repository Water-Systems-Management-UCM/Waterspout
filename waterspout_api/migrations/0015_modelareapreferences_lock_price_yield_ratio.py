# Generated by Django 3.2 on 2021-04-07 00:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0014_auto_20210406_1439'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelareapreferences',
            name='lock_price_yield_ratio',
            field=models.BooleanField(default=False),
        ),
    ]