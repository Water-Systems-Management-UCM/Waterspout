import logging
import json

from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import status
from rest_framework import permissions

from waterspout_api import models

log = logging.getLogger("waterspout.permissions")


class IsInSameOrganization(permissions.BasePermission):
	"""
		Can only be used on objects that have an "organization" property
	"""

	def has_permission(self, request, view):
		if request.method in permissions.SAFE_METHODS:
			return True  # in this case, we can't really check permissions here - need to make sure the queryset filters properly
		else:
			return self._check_org_info(request.user, request.data, view)

	def has_object_permission(self, request, view, obj):
		if request.method in permissions.SAFE_METHODS:  # org members can read
			return obj.organization.has_member(request.user)
		else:
			return self._check_org_info(request.user, request.data, view)

	def _check_org_info(self, request_user, request_data, view):
		# get the item ID, as well as the class of the item so we can look the item up.
		# We assume this permission is only used for items that have an "organization" foreign key
		if "pk" in view.kwargs:  # then we're checking against an existing object
			item_id = view.kwargs['pk']
			item_class = view.serializer_class.Meta.model
			try:
				item = item_class.objects.get(pk=item_id)
			except item_class.DoesNotExist:
				return PermissionError("Model Run doesn't exist")

			if hasattr(item, "organization"):
				organization = item.organization
			elif hasattr(item, "model_area"):
				organization = item.model_area.organization
			elif hasattr(item, "model_run"):
				organization = item.model_run.organization
			elif hasattr(item, "calibration_set"):
				organization = item.calibration_set.model_area.organization

		else:  # we're creating an object - check what org they specify instead of the org of the object
			if type(request_data) is not dict:
				request_data = json.loads(request_data)
			organization = models.Organization.objects.get(id=int(request_data["organization"]))

		#log.debug(f"Make Model Run Request: ${request_data}")

		# Check Permissions
		if not organization.has_member(request_user):
			log.error("User is not a member of the specified organization and cannot create or modify model runs within it")
			raise PermissionDenied(
				"User is not a member of the specified organization and cannot create or modify model runs within it")
		# request_data["organization"] = organization  # replace it with the object so we can assign it later

		if "calibration_set" in request_data:
			calibration_set = models.CalibrationSet.objects.get(id=int(request_data["calibration_set"]))
			log.debug(f"Calibration Set: {calibration_set}")
			if not calibration_set.model_area.organization == organization:
				log.error("CalibrationSet is not part of this organization. You can only use calibration sets that"
				          "are attached to the organization you're working within")
				raise PermissionDenied(
					detail="CalibrationSet is not part of this organization. You can only use calibration sets that"
					       "are attached to the organization you're working within")
			# request_data["calibration_set"] = calibration_set  # replace it with the object so we can assign it later

		return True


class CanCreateOrModifyModelRuns(permissions.BasePermission):
	def has_permission(self, request, view):
		if request.method in permissions.SAFE_METHODS:  # allow them to read model runs with this permission
			return True
		else:  # but if they want to create, we need to check if the ModelArea allows creation
			if "pk" in view.kwargs:  # then we're checking against an existing object
				item_id = view.kwargs['pk']
				item_class = view.serializer_class.Meta.model
				try:
					item = item_class.objects.get(pk=item_id)
				except item_class.DoesNotExist:
					return PermissionError("Model Run doesn't exist")

				if hasattr(item, "model_area"):
					model_area = item.model_area
				elif hasattr(item, "calibration_set"):
					model_area = item.calibration_set.model_area
				else:
					raise RuntimeError(f"Can't get model area from {view.serializer_class}")
			else:
				if type(request.data) is not dict:
					request_data = json.loads(request.data)
				else:
					request_data = request.data
				calibration_set = models.CalibrationSet.objects.get(pk=request_data["calibration_set"])
				model_area = calibration_set.model_area

			preferences = model_area.preferences
			return preferences.create_or_modify_model_runs