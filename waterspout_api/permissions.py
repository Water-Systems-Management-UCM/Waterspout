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

	def has_object_permission(self, request, view, obj):

		if request.method in permissions.SAFE_METHODS:  # if we're doing a GET/HEAD/OPTIONS request to read an object
			return obj.organization.has_member(request.user)

		# otherwise, if we're creating, we need to check more of the specifics of the request
		request_data = request.data
		if type(request_data) is not dict:
			request_data = json.loads(request_data)

		log.debug(f"Make Model Run Request: ${request_data}")

		# Check Permissions
		organization = models.Organization.objects.get(id=int(request_data["organization"]))
		if not organization.has_member(request.user):
			log.error("User is not a member of the specified organization and cannot create model runs within it")
			raise PermissionDenied(
				"User is not a member of the specified organization and cannot create model runs within it")
		#request_data["organization"] = organization  # replace it with the object so we can assign it later

		calibration_set = models.CalibrationSet.objects.get(id=int(request_data["calibration_set"]))
		log.debug(f"Calibration Set: {calibration_set}")
		if not calibration_set.model_area.organization == organization:
			log.error("CalibrationSet is not part of this organization. You can only use calibration sets that"
			          "are attached to the organization you're working within")
			raise PermissionDenied(
				detail="CalibrationSet is not part of this organization. You can only use calibration sets that"
				       "are attached to the organization you're working within")
		#request_data["calibration_set"] = calibration_set  # replace it with the object so we can assign it later

		return True