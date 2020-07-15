import json
import logging

from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer


from waterspout_api import models

log = logging.getLogger("waterspout.serializers")

class RegionSerializer(serializers.ModelSerializer):
	geometry = serializers.JSONField(read_only=True, binary=False)

	class Meta:
		model = models.Region
		fields = '__all__'


class RegionModificationSerializer(serializers.ModelSerializer):

	class Meta:
		fields = models.RegionModification.serializer_fields
		model = models.RegionModification
		depth = 2


class ModelRunSerializer(serializers.ModelSerializer):
	region_modifications = RegionModificationSerializer(allow_null=True, many=True)

	class Meta:
		model = models.ModelRun
		fields = models.ModelRun.serializer_fields + ['region_modifications']
		depth = 2

	def create(self, validated_data):
		region_modification_data = validated_data.pop('region_modifications')
		model_run = models.ModelRun.objects.create(**validated_data)
		for modification in region_modification_data:
			models.RegionModification.objects.create(model_run=model_run, **modification)
		return model_run