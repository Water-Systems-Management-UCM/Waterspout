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


class UsersSerializer(serializers.ModelSerializer):

	class Meta:
		fields = ["username", "id"]
		model = models.User


class UserProfileSerializer(serializers.ModelSerializer):
	class Meta:
		fields = models.UserProfile._serializer_fields
		model = models.UserProfile

	def update(self, instance, validated_data):
		for key in validated_data:
			# assign the data from the serializer, or use the value the instance already has
			setattr(instance, key, validated_data.get(key, getattr(instance, key)))
		instance.save()
		return instance


class CropModificationSerializer(serializers.ModelSerializer):

	class Meta:
		fields = models.CropModification.serializer_fields
		model = models.CropModification


class ResultSerializer(serializers.ModelSerializer):
	"""
		For a single result - we'll basically never access this endpoint, but we'll use it to define the fields for the
		full RunResultSerializer
	"""

	class Meta:
		fields = settings.LIMITED_RESULTS_FIELDS
		model = models.Result


class InfeasibilitySerializer(serializers.ModelSerializer):

	class Meta:
		fields = "__all__"
		model = models.Infeasibility


class ResultSetSerializer(serializers.ModelSerializer):
	"""
		For a single result - we'll basically never access this endpoint, but we'll use it to define the fields for the
		full RunResultSerializer
	"""
	result_set = ResultSerializer(allow_null=True, many=True)
	infeasibilities = InfeasibilitySerializer(allow_null=True, many=True, read_only=True)

	class Meta:
		fields = ["result_set", "dapper_version", "infeasibilities", "infeasibilities_text"]
		model = models.ResultSet


class ModelRunSerializer(ModelActionSerializer):
	region_modifications = RegionModificationSerializer(allow_null=True, many=True)
	crop_modifications = CropModificationSerializer(allow_null=True, many=True)
	results = ResultSetSerializer(allow_null=True)

	class Meta:
		model = models.ModelRun
		_base_fields = models.ModelRun.serializer_fields + ['region_modifications', 'crop_modifications']
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
		crop_modification_data = validated_data.pop('crop_modifications')

		model_run = models.ModelRun.objects.create(**validated_data)
		for modification in region_modification_data:
			models.RegionModification.objects.create(model_run=model_run, **modification)
		for modification in crop_modification_data:
			models.CropModification.objects.create(model_run=model_run, **modification)
		return model_run


class CalibrationItemSerializer(serializers.ModelSerializer):
	"""
		Provides access to a single input data record for viewing the database
	"""
	class Meta:
		fields = models.CalibratedParameter.serializer_fields
		model = models.CalibratedParameter


class CalibrationSetSerializer(serializers.ModelSerializer):
	"""
		Provides access to the input data records for viewing the database, but is also how we'll
		retrieve the list of model runs
	"""
	# calibration_set = CalibrationItemSerializer(read_only=True, many=True)
	model_runs = ModelRunSerializer(read_only=True, many=True)

	class Meta:
		fields = ["model_runs"]
		model = models.CalibrationSet

		depth = 0


class InputDataItemSerializer(serializers.ModelSerializer):
	"""
		Provides access to a single input data record for viewing the database
	"""
	class Meta:
		fields = models.InputDataItem.serializer_fields
		model = models.InputDataItem


class InputDataSetSerializer(serializers.ModelSerializer):
	"""
		Provides access to the input data records for viewing the database, but is also how we'll
		retrieve the list of model runs
	"""
	input_data_set = InputDataItemSerializer(read_only=True, many=True)

	class Meta:
		fields = ["input_data_set"]
		model = models.InputDataSet

		depth = 0


class ModelAreaSerializer(ModelActionSerializer):
	calibration_data = CalibrationSetSerializer(read_only=True, many=True, allow_null=True)
	input_data = InputDataSetSerializer(read_only=True, many=True, allow_null=True)
	crop_set = CropSerializer(read_only=True, many=True, allow_null=True)
	region_set = RegionSerializer(read_only=True, many=True, allow_null=True)

	class Meta:
		model = models.ModelArea
		_base_fields = ["id", "organization_id", "name", "description", "map_center_latitude",
		                "map_center_longitude", "map_default_zoom", "model_defaults"]
		fields = _base_fields
		action_fields = {  # only send model results in detail view - that way the listing doesn't send massive amount
			"retrieve": {     # of data, but we only need to load the specific model run again to get the results
				"fields": _base_fields + ["calibration_data", "input_data", "crop_set", "region_set"]
			}
		}
		depth = 0  # will still show objects that are explicitly declared as nested objects (like region_modifications)
					# this lets us say "I don't want region geometries here" while still getting the modifications in one request
