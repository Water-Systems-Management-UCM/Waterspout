# Generated by Django 3.2 on 2021-05-05 21:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0037_auto_20210505_1058'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rainfallparameter',
            name='omegacash',
        ),
        migrations.RemoveField(
            model_name='rainfallparameter',
            name='omegaestablish',
        ),
        migrations.RemoveField(
            model_name='rainfallparameter',
            name='omegalabor',
        ),
        migrations.RemoveField(
            model_name='rainfallparameter',
            name='omegaland',
        ),
        migrations.RemoveField(
            model_name='rainfallparameter',
            name='omeganoncash',
        ),
        migrations.RemoveField(
            model_name='rainfallparameter',
            name='omegasupply',
        ),
        migrations.RemoveField(
            model_name='rainfallparameter',
            name='omegatotal',
        ),
        migrations.RemoveField(
            model_name='result',
            name='omegacash',
        ),
        migrations.RemoveField(
            model_name='result',
            name='omegaestablish',
        ),
        migrations.RemoveField(
            model_name='result',
            name='omegalabor',
        ),
        migrations.RemoveField(
            model_name='result',
            name='omegaland',
        ),
        migrations.RemoveField(
            model_name='result',
            name='omeganoncash',
        ),
        migrations.RemoveField(
            model_name='result',
            name='omegasupply',
        ),
        migrations.RemoveField(
            model_name='result',
            name='omegatotal',
        ),
    ]
