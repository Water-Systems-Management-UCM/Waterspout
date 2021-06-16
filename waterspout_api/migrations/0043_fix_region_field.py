from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0042_change_modeled_type_to_macro'),
    ]

    operations = [
        migrations.AlterField(
            model_name='region',
            name='default_behavior',
            field=models.SmallIntegerField(choices=[(1, 'Modeled'), (2, 'Removed'), (3, 'Fixed')], default=0),
        ),
    ]
