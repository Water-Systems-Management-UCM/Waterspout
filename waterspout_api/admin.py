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


class ModelRunRegionModificationInline(admin.TabularInline):
    model = models.RegionModification


class ModelRunAdmin(admin.ModelAdmin):
    inlines = [ModelRunRegionModificationInline]


admin.site.register(models.ModelRun, ModelRunAdmin)
admin.site.register(models.RegionModification)
admin.site.register(models.ResultSet)
