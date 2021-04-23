# Generated by Django 3.2 on 2021-04-23 03:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0022_auto_20210421_1608'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegionMultipliers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_revenue', models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True)),
                ('direct_value_add', models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True)),
                ('total_value_add', models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True)),
                ('direct_jobs', models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True)),
                ('total_jobs', models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True)),
                ('region', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='multipliers', to='waterspout_api.region')),
            ],
        ),
    ]
