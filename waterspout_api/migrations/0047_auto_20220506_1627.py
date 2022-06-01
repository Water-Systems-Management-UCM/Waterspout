# Generated by Django 3.2.13 on 2022-05-06 23:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0046_modelareapreferences_shared_model_runs'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='net_revenue_pmp_yield',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='net_revenue_red_costs',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=18, null=True),
        ),
    ]