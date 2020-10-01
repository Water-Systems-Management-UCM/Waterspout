import json
import logging

from rest_framework import serializers
from action_serializer import ModelActionSerializer

from Waterspout import settings
from waterspout_api import models

log = logging.getLogger("waterspout.serializers")


class CropSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.Crop
		fields = '__all__'


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

	result_set = ResultSerializer(allow_null=True, many=True)

	class Meta:
		fields = ["result_set"]
		model = models.ResultSet


class ModelRunSerializer(ModelActionSerializer):
	region_modifications = RegionModificationSerializer(allow_null=True, many=True)
	results = ResultSetSerializer(allow_null=True)

	class Meta:
		model = models.ModelRun
		_base_fields = models.ModelRun.serializer_fields + ['region_modifications']
		fields = _base_fields
		action_fields = {  # only send model results in detail view - that way the listing doesn't send massive amount
			"retrieve": {     # of data, but we only need to load the specific model run again to get the results
				"fields": _base_fields + ['results']
			}
		}
		depth = 0  # will still show objects that are explicitly declared as nested objects (like region_modifications)
					# this lets us say "I don't want region geometries here" while still getting the modifications in one request

	def create(self, validated_data):
		region_modification_data = validated_data.pop('region_modifications')

		model_run = models.ModelRun.objects.create(**validated_data)
		for modification in region_modification_data:
			models.RegionModification.objects.create(model_run=model_run, **modification)
		return model_run