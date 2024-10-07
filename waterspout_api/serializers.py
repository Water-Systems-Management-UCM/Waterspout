import json
import logging

from rest_framework import serializers
from action_serializer import ModelActionSerializer
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.hashers import check_password
from Waterspout import settings
from waterspout_api import models

log = logging.getLogger("waterspout.serializers")



class CropSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.Crop
		fields = '__all__'


class EmploymentMultipliersSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.EmploymentMultipliers
		fields = "__all__"


class RegionSerializer(serializers.ModelSerializer):
	geometry = serializers.JSONField(read_only=True, binary=False)

	class Meta:
		model = models.Region
		fields = models.Region.serializer_fields


class RegionGroupSerializer(serializers.ModelSerializer):
	geometry = serializers.JSONField(read_only=True, binary=False)

	class Meta:
		model = models.RegionGroup
		fields = models.RegionGroup.serializer_fields


class RegionGroupSetSerializer(serializers.ModelSerializer):
	groups = RegionGroupSerializer(read_only=True, many=True, allow_null=True)

	class Meta:
		model = models.RegionGroupSet
		fields = models.RegionGroupSet.serializer_fields


class RegionModificationSerializer(serializers.ModelSerializer):

	class Meta:
		fields = models.RegionModification.serializer_fields
		model = models.RegionModification


class UsersSerializer(serializers.ModelSerializer):

	class Meta:
		fields = ["username", "id"]
		model = models.User


class UserProfileSerializer(serializers.ModelSerializer):
	user = UsersSerializer(read_only=True)

	class Meta:
		fields = models.UserProfile._serializer_fields
		model = models.UserProfile
		depth = 1

	def update(self, instance, validated_data):
		for key in validated_data:
			if key == "user":  # make sure we ignore anything that's part of the user object itself
				continue
			# assign the data from the serializer, or use the value the instance already has
			setattr(instance, key, validated_data.get(key, getattr(instance, key)))
		instance.save()
		return instance


class EmailSerializer(serializers.Serializer):
	email = serializers.EmailField()

	class Meta:
		fields = ("email",)


class ResetPasswordSerializer(serializers.Serializer):
	password = serializers.CharField(
		write_only=True
	)

	class Meta:
		fields = ("password",)

	def validate(self, data):

		# user's new password
		password = data.get("password")
		kwargs = self.context.get("kwargs", {})
		token = kwargs.get("token")
		encoded_pk = kwargs.get("encoded_pk")

		if token is None:
			raise serializers.ValidationError("Missing token")
		elif encoded_pk is None:
			raise serializers.ValidationError("Missing encoded_pk")

		pk = urlsafe_base64_decode(encoded_pk).decode()
		user = get_user_model().objects.get(pk=pk)

		if PasswordResetTokenGenerator().check_token(user, token):
			user.set_password(password)
			user.save()
			return data
		else:
			raise serializers.ValidationError("Token is not valid")


class ChangePasswordSerializer(serializers.Serializer):
	password = serializers.CharField(
		write_only=True
	)

	class Meta:
		model = get_user_model()
		fields = ("password", "token", "old_password")

	def validate(self, data):
		kwargs = self.context.get("kwargs", {})
		token = kwargs.get("token")
		old_password = kwargs.get("old_password")

		if token is None:
			raise serializers.ValidationError("Missing token")
		elif old_password is None:
			raise serializers.ValidationError("Missing encoded_pk")

		return data  # Then proceed to updating password

	def update(self, instance, validated_data):
		instance.set_password(validated_data.get('password'))
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


class RainfallResultSerializer(serializers.ModelSerializer):
	"""
		For a single result - we'll basically never access this endpoint, but we'll use it to define the fields for the
		full RunResultSerializer
	"""

	class Meta:
		fields = models.RainfallResult.serializer_fields
		model = models.RainfallResult

class RainfallItemSerializer(serializers.ModelSerializer):
	"""
		For a single result - we'll basically never access this endpoint, but we'll use it to define the fields for the
		full RunResultSerializer
	"""

	class Meta:
		fields = "__all__"
		model = models.RainfallParameter


class RainfallSetSerializer(serializers.ModelSerializer):
	"""
		Provides access to the input data records for viewing the database, but is also how we'll
		retrieve the list of model runs
	"""
	rainfall_set = RainfallItemSerializer(read_only=True, many=True)

	class Meta:
		fields = ["id", "rainfall_set"] #, "model_runs"]
		model = models.RainfallSet

		depth = 0

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
	rainfall_result_set = RainfallResultSerializer(allow_null=True, many=True)
	infeasibilities = InfeasibilitySerializer(allow_null=True, many=True, read_only=True)

	class Meta:
		fields = ["result_set", "rainfall_result_set", "in_calibration", "dapper_version", "date_run", "infeasibilities", "infeasibilities_text"]
		model = models.ResultSet


class ModelRunSerializer(ModelActionSerializer):
	#region_modifications = serializers.SerializerMethodField()
	region_modifications = RegionModificationSerializer(allow_null=True, many=True)
	crop_modifications = CropModificationSerializer(allow_null=True, many=True)
	results = serializers.SerializerMethodField()  # forces it to get looked up below and lets us sort them by date

	"""def get_region_modifications(self, model_run):
		queryset = model_run.region_modifications.filter(created_from_group=False)
		region_modifications = RegionModificationSerializer(instance=queryset, allow_null=True, many=True)
		return region_modifications.data"""

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

	def update(self, instance, validated_data):
		instance.name = validated_data.get('name', instance.name)
		instance.description = validated_data.get('description', instance.description)
		instance.save()
		return instance

	def get_results(self, instance):
		"""
			We can have multiple result sets for each model run. This function retrieves the results sets
			and orders them by date, descending. This ensures that the newest results for the model run are always
			in position 0 in the web app so that it can start with index 0 and not need to examine which is newest itself.
			Users will see the newest by default until we can add functionality for them to switch it.
		:param instance:
		:return:
		"""
		results = instance.results.all().order_by('-date_run')
		return ResultSetSerializer(results, allow_null=True, many=True).data

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
	calibration_set = CalibrationItemSerializer(read_only=True, many=True)
	#model_runs = ModelRunSerializer(read_only=True, many=True)

	class Meta:
		fields = ["id", "calibration_set"] #, "model_runs"]
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


class ModelAreaPreferencesSerializer(serializers.ModelSerializer):
	class Meta:
		fields = "__all__"
		model = models.ModelAreaPreferences


class ModelAreaMultipliersSerializer(serializers.ModelSerializer):
	class Meta:
		fields = "__all__"
		model = models.EmploymentMultipliers


class ModelAreaSerializer(ModelActionSerializer):
	calibration_data = CalibrationSetSerializer(read_only=True, many=True, allow_null=True)
	rainfall_data = RainfallSetSerializer(read_only=True, many=True, allow_null=True)
	input_data = InputDataSetSerializer(read_only=True, many=True, allow_null=True)
	crop_set = CropSerializer(read_only=True, many=True, allow_null=True)
	region_set = RegionSerializer(read_only=True, many=True, allow_null=True)
	region_group_sets = RegionGroupSetSerializer(read_only=True, many=True, allow_null=True)
	multipliers_raw = serializers.SerializerMethodField(read_only=True)
	preferences = ModelAreaPreferencesSerializer(read_only=True)

	class Meta:
		model = models.ModelArea
		_base_fields = ["id", "organization_id", "name", "description", "map_center_latitude",
		                "map_center_longitude", "map_default_zoom", "model_defaults", "preferences"]
		fields = _base_fields
		action_fields = {  # only send model results in detail view - that way the listing doesn't send massive amount
			"retrieve": {     # of data, but we only need to load the specific model run again to get the results
				"fields": _base_fields + ["main_help_page_content", "calibration_data", "rainfall_data", "input_data",
				                          "crop_set", "region_set", "region_group_sets", "multipliers_raw",
		                                    "supports_rainfall", "supports_irrigation", "background_code"]
			}
		}
		depth = 0  # will still show objects that are explicitly declared as nested objects (like region_modifications)
					# this lets us say "I don't want region geometries here" while still getting the modifications in one request

	def get_multipliers_raw(self, instance):
		multipliers = models.EmploymentMultipliers.objects.filter(region__model_area=instance)
		return EmploymentMultipliersSerializer(multipliers, read_only=True, allow_null=True, many=True).data