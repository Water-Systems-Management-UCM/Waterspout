# Generated by Django 3.2.13 on 2022-05-25 21:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0051_auto_20220513_1228'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='regiongroupset',
            unique_together={('name', 'model_area')},
        ),
    ]