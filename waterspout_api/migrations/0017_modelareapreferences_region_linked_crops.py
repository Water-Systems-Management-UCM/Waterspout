# Generated by Django 3.2 on 2021-04-12 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0016_modelareapreferences_include_net_revenue'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelareapreferences',
            name='region_linked_crops',
            field=models.BooleanField(default=True),
        ),
    ]
