# Generated by Django 3.1 on 2021-03-18 20:33

from django.db import migrations, models
import django.db.models.deletion


def create_model_area_preferences(apps, schema_editor, **kwargs):
    """
        Make sure that all existing model areas have preference objects assigned
    :param apps:
    :param kwargs:
    :return:
    """
    ModelArea = apps.get_model("waterspout_api", "ModelArea")
    ModelAreaPreferences = apps.get_model("waterspout_api", "ModelAreaPreferences")

    for area in ModelArea.objects.all():
        ModelAreaPreferences.objects.create(model_area=area)

class Migration(migrations.Migration):

    dependencies = [
        ('waterspout_api', '0011_auto_20210316_1548'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelAreaPreferences',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enforce_price_yield_constraints', models.BooleanField(default=True)),
                ('model_area', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='waterspout_api.modelarea')),
            ],
        ),
        migrations.RunPython(create_model_area_preferences)
    ]