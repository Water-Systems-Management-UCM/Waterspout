# Generated by Django 3.1 on 2020-12-02 23:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0004_auto_20201202_1358'),
    ]

    operations = [
        migrations.AddField(
            model_name='region',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]