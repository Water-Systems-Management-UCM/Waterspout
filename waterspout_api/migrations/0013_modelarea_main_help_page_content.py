# Generated by Django 3.1 on 2021-03-31 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0012_modelareapreferences'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelarea',
            name='main_help_page_content',
            field=models.TextField(blank=True, null=True),
        ),
    ]
