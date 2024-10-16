# Generated by Django 3.2 on 2021-04-30 22:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0033_auto_20210430_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='rainfallparameter',
            name='pespr',
            field=models.DecimalField(decimal_places=5, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='rainfallparameter',
            name='pesum',
            field=models.DecimalField(decimal_places=5, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='rainfallparameter',
            name='pewin',
            field=models.DecimalField(decimal_places=5, default=0, max_digits=10),
            preserve_default=False,
        ),
    ]
