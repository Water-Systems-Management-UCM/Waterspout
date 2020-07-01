import os
import json
import logging

from django.contrib.auth.models import User, Group

from rest_framework.test import APITestCase, APIRequestFactory, APITransactionTestCase
from rest_framework import status

from waterspout_api.load import dap
from waterspout_api import support, models
from . import TEST_DATA_FOLDER

log = logging.getLogger("waterspout.tests")

class APIModelRunTestCase(APITransactionTestCase):

	def setUp(self):
		#dap.load_dap()  # need to replace this with fixtures at some point
		self.factory = APIRequestFactory()

		self.group = Group()
		self.group.save()
		self.organization = models.Organization(group=self.group)
		self.organization.save()
		self.model_area = models.ModelArea(name="test")
		self.model_area.save()
		self.calibration_set = models.CalibrationSet(model_area=self.model_area)
		self.calibration_set.save()

		self.test_request_data = {
			"ready": False,
		    "calibrated_parameters_text": "NA",
			"calibration_set": self.calibration_set.id,
			"organization": self.organization.id
		}

		log.info(f"Request is {str(self.test_request_data)}")

		# the URL here should be a call to `reverse` instead of hardcoded
		self.url = '/api/model_runs/'

	def test_nonmember_user_fails(self):
		# new user has no permissions, but is authenticated
		new_user = User()
		new_user.save()
		self.client.force_authenticate(user=new_user)  # set the authentication - no tokens needed

		response = self.client.post(self.url, json.dumps(self.test_request_data), format="json")
		# should be getting a PermissionError because user isn't in the right group
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_member_calibration_set_fails(self):
		# new user is now a group member
		new_user = User()
		new_user.save()
		new_user.groups.add(self.organization.group)
		new_user.save()

		self.client.force_authenticate(user=new_user)  # set the authentication - no tokens needed

		response = self.client.post(self.url, json.dumps(self.test_request_data), format="json")
		# should be getting a PermissionError because calibration set isn't in an organization the user is a part of
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

		# make the calibration set happen within this organization
		self.model_area.organization = self.organization
		self.model_area.save()

		response = self.client.post(self.url, json.dumps(self.test_request_data), format="json")
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

	# test that user that's not a member of the group gets PermissionDenied
	# test that use of calibration set that's not in org gets PermissionDenied
	# test that use of calibration set and user in org succeeds and returns HTTP 200 and a status message
	# test that patching an existing item has same behavior