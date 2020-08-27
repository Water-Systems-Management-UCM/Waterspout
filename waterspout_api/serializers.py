import json
import logging

from rest_framework import serializers

from Waterspout import settings
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


class ResultSerializer(serializers.ModelSerializer):
	"""
		For a single result - we'll basically never access this endpoint, but we'll use it to define the fields for the
		full RunResultSerializer
	"""

	class Meta:
		fields = settings.LIMITED_RESULTS_FIELDS
		model = models.Result


class ResultSetSerializer(serializers.ModelSerializer):
	"""
		For a single result - we'll basically never access this endpoint, but we'll use it to define the fields for the
		full RunResultSerializer
	"""

	results = ResultSerializer(allow_null=True, many=True)

	class Meta:
		fields = ["results"]
		model = models.ResultSet


class ModelRunSerializer(serializers.ModelSerializer):
	region_modifications = RegionModificationSerializer(allow_null=True, many=True)

	class Meta:
		model = models.ModelRun
		fields = models.ModelRun.serializer_fields + ['region_modifications']
		depth = 0  # will still show objects that are explicitly declared as nested objects (like region_modifications)
					# this lets us say "I don't want region geometries here" while still getting the modifications in one request

	def create(self, validated_data):
		region_modification_data = validated_data.pop('region_modifications')

		model_run = models.ModelRun.objects.create(**validated_data)
		for modification in region_modification_data:
			models.RegionModification.objects.create(model_run=model_run, **modification)
		return model_run