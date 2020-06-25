# Generated by Django 3.0.6 on 2020-06-25 20:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalibrationSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('years', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Crop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('crop_code', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='CropGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('crops', models.ManyToManyField(to='waterspout_api.Crop')),
            ],
        ),
        migrations.CreateModel(
            name='ModelArea',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('internal_id', models.CharField(max_length=100, unique=True)),
                ('external_id', models.CharField(blank=True, max_length=100, null=True)),
                ('geometry', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RegionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('internal_id', models.CharField(max_length=100)),
                ('geometry', models.TextField(blank=True, null=True)),
                ('model_area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='waterspout_api.ModelArea')),
            ],
        ),
        migrations.CreateModel(
            name='ResultSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('years', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.CharField(max_length=10)),
                ('omegaland', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omegasupply', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omegalabor', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omegaestablish', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omegacash', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omeganoncash', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omegatotal', models.DecimalField(decimal_places=1, max_digits=10)),
                ('xwater', models.DecimalField(decimal_places=10, max_digits=18)),
                ('p', models.DecimalField(decimal_places=10, max_digits=18)),
                ('y', models.DecimalField(decimal_places=5, max_digits=13)),
                ('xland', models.DecimalField(decimal_places=10, max_digits=18)),
                ('omegawater', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sigma', models.DecimalField(decimal_places=4, max_digits=5)),
                ('theta', models.DecimalField(decimal_places=4, max_digits=5)),
                ('pimarginal', models.DecimalField(decimal_places=10, max_digits=18)),
                ('alphaland', models.DecimalField(decimal_places=10, max_digits=11)),
                ('alphawater', models.DecimalField(decimal_places=10, max_digits=11)),
                ('alphasupply', models.DecimalField(decimal_places=10, max_digits=11)),
                ('alphalabor', models.DecimalField(decimal_places=10, max_digits=11)),
                ('rho', models.DecimalField(decimal_places=10, max_digits=15)),
                ('lambdaland', models.DecimalField(decimal_places=10, max_digits=15)),
                ('lambdacrop', models.DecimalField(decimal_places=10, max_digits=15)),
                ('betaland', models.DecimalField(decimal_places=10, max_digits=18)),
                ('betawater', models.DecimalField(decimal_places=10, max_digits=18)),
                ('betasupply', models.DecimalField(decimal_places=10, max_digits=18)),
                ('betalabor', models.DecimalField(decimal_places=10, max_digits=18)),
                ('tau', models.DecimalField(decimal_places=10, max_digits=18)),
                ('gamma', models.DecimalField(decimal_places=10, max_digits=18)),
                ('delta', models.DecimalField(decimal_places=10, max_digits=18)),
                ('xlandcalib', models.DecimalField(decimal_places=10, max_digits=18)),
                ('xwatercalib', models.DecimalField(decimal_places=10, max_digits=18)),
                ('difflandpct', models.DecimalField(decimal_places=10, max_digits=12)),
                ('diffwaterpct', models.DecimalField(decimal_places=10, max_digits=12)),
                ('g', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='waterspout_api.Region')),
                ('i', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='waterspout_api.Crop')),
                ('result_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='result_set', to='waterspout_api.ResultSet')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RegionExtra',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('value', models.TextField(blank=True, null=True)),
                ('data_type', models.CharField(max_length=5)),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='extra_attributes', to='waterspout_api.Region')),
            ],
        ),
        migrations.AddField(
            model_name='region',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='waterspout_api.RegionGroup'),
        ),
        migrations.AddField(
            model_name='region',
            name='model_area',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='waterspout_api.ModelArea'),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('group', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='auth.Group')),
            ],
        ),
        migrations.CreateModel(
            name='ModelRun',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ready', models.BooleanField(default=False)),
                ('running', models.BooleanField(default=False)),
                ('complete', models.BooleanField(default=False)),
                ('status_message', models.CharField(blank=True, default='', max_length=2048, null=True)),
                ('result_values', models.TextField(blank=True, default='', null=True)),
                ('log_data', models.TextField(blank=True, null=True)),
                ('date_submitted', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('date_completed', models.DateTimeField(blank=True, null=True)),
                ('calibrated_parameters_text', models.TextField()),
                ('calibration_set', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='waterspout_api.CalibrationSet')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='model_runs', to='waterspout_api.Organization')),
                ('results', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='model_run', to='waterspout_api.ResultSet')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='model_runs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='modelarea',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='waterspout_api.Organization'),
        ),
        migrations.AddField(
            model_name='crop',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='waterspout_api.Organization'),
        ),
        migrations.AddField(
            model_name='calibrationset',
            name='model_area',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='waterspout_api.ModelArea'),
        ),
        migrations.CreateModel(
            name='CalibratedParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.CharField(max_length=10)),
                ('omegaland', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omegasupply', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omegalabor', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omegaestablish', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omegacash', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omeganoncash', models.DecimalField(decimal_places=1, max_digits=10)),
                ('omegatotal', models.DecimalField(decimal_places=1, max_digits=10)),
                ('xwater', models.DecimalField(decimal_places=10, max_digits=18)),
                ('p', models.DecimalField(decimal_places=10, max_digits=18)),
                ('y', models.DecimalField(decimal_places=5, max_digits=13)),
                ('xland', models.DecimalField(decimal_places=10, max_digits=18)),
                ('omegawater', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sigma', models.DecimalField(decimal_places=4, max_digits=5)),
                ('theta', models.DecimalField(decimal_places=4, max_digits=5)),
                ('pimarginal', models.DecimalField(decimal_places=10, max_digits=18)),
                ('alphaland', models.DecimalField(decimal_places=10, max_digits=11)),
                ('alphawater', models.DecimalField(decimal_places=10, max_digits=11)),
                ('alphasupply', models.DecimalField(decimal_places=10, max_digits=11)),
                ('alphalabor', models.DecimalField(decimal_places=10, max_digits=11)),
                ('rho', models.DecimalField(decimal_places=10, max_digits=15)),
                ('lambdaland', models.DecimalField(decimal_places=10, max_digits=15)),
                ('lambdacrop', models.DecimalField(decimal_places=10, max_digits=15)),
                ('betaland', models.DecimalField(decimal_places=10, max_digits=18)),
                ('betawater', models.DecimalField(decimal_places=10, max_digits=18)),
                ('betasupply', models.DecimalField(decimal_places=10, max_digits=18)),
                ('betalabor', models.DecimalField(decimal_places=10, max_digits=18)),
                ('tau', models.DecimalField(decimal_places=10, max_digits=18)),
                ('gamma', models.DecimalField(decimal_places=10, max_digits=18)),
                ('delta', models.DecimalField(decimal_places=10, max_digits=18)),
                ('xlandcalib', models.DecimalField(decimal_places=10, max_digits=18)),
                ('xwatercalib', models.DecimalField(decimal_places=10, max_digits=18)),
                ('difflandpct', models.DecimalField(decimal_places=10, max_digits=12)),
                ('diffwaterpct', models.DecimalField(decimal_places=10, max_digits=12)),
                ('calibration_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calibration_set', to='waterspout_api.CalibrationSet')),
                ('g', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='waterspout_api.Region')),
                ('i', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='waterspout_api.Crop')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RegionModification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('water_proportion', models.FloatField()),
                ('land_proportion', models.FloatField()),
                ('model_run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='region_modifications', to='waterspout_api.ModelRun')),
                ('region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='modifications', to='waterspout_api.Region')),
                ('region_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='modifications', to='waterspout_api.RegionGroup')),
            ],
            options={
                'unique_together': {('model_run', 'region')},
            },
        ),
        migrations.CreateModel(
            name='CropModification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price_proportion', models.FloatField()),
                ('yield_proportion', models.FloatField()),
                ('min_land_area_proportion', models.FloatField()),
                ('max_land_area_proportion', models.FloatField()),
                ('crop', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='modifications', to='waterspout_api.Crop')),
                ('crop_group', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='modifications', to='waterspout_api.CropGroup')),
                ('model_run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='crop_modifications', to='waterspout_api.ModelRun')),
            ],
            options={
                'unique_together': {('model_run', 'crop')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='crop',
            unique_together={('crop_code', 'organization')},
        ),
    ]
