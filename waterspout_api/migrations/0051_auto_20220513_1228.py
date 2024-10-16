# Generated by Django 3.2.13 on 2022-05-13 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0050_auto_20220511_1120'),
    ]

    operations = [
        migrations.AddField(
            model_name='regionmodification',
            name='created_from_group',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(
            name='regionmodification',
            unique_together={('model_run', 'region', 'region_group')},
        ),
    ]
