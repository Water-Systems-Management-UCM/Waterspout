from rest_framework import serializers

from waterspout_api import models


class RegionSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = models.Region
		fields = ['name', 'internal_id', 'external_id', 'geometry']


class ModelRunSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = models.ModelRun
		fields = models.ModelRun.serializer_fields