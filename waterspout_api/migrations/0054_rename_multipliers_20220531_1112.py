
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0053_load_dap_region_groups'),
    ]

    operations = [
        migrations.RenameModel('RegionMultipliers', 'EmploymentMultipliers'),
        migrations.AddField('EmploymentMultipliers', 'crop', field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='multipliers', null=True,
                                           to='waterspout_api.crop')),
    ]
