# Generated by Django 3.1 on 2020-12-15 23:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0006_userprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calibratedparameter',
            name='omegacash',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='calibratedparameter',
            name='omegaestablish',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='calibratedparameter',
            name='omeganoncash',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='calibratedparameter',
            name='omegatotal',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='inputdataitem',
            name='omegacash',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='inputdataitem',
            name='omegaestablish',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='inputdataitem',
            name='omeganoncash',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='inputdataitem',
            name='omegatotal',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='omegacash',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='omegaestablish',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='omeganoncash',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='omegatotal',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True),
        ),
    ]
