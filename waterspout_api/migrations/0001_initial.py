# Generated by Django 3.0.6 on 2020-06-02 20:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CalibratedParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
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
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='RegionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('internal_id', models.CharField(max_length=100)),
                ('geometry', models.TextField(blank=True, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='waterspout_api.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('internal_id', models.CharField(max_length=100)),
                ('geometry', models.TextField(blank=True, null=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='waterspout_api.RegionGroup')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='waterspout_api.Organization')),
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
        migrations.AddField(
            model_name='crop',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='waterspout_api.Organization'),
        ),
    ]
