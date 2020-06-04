from django.contrib import admin
from waterspout_api import models
# Register your models here.

admin.site.register(models.Organization)
admin.site.register(models.ModelArea)
admin.site.register(models.RegionGroup)
admin.site.register(models.Region)
admin.site.register(models.RegionExtra)
admin.site.register(models.CropGroup)
admin.site.register(models.Crop)
admin.site.register(models.CalibrationSet)
admin.site.register(models.CalibratedParameter)
admin.site.register(models.ModelRun)
admin.site.register(models.RegionModification)
