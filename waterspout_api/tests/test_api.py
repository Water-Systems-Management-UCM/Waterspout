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
			"calibration_set": self.calibration_set.id,
			"organization": self.organization.id,
			"region_modifications": [],
			"crop_modifications": [],
			"name": "test",
		}

		log.info(f"Request is {str(self.test_request_data)}")

		# the URL here should be a call to `reverse` instead of hardcoded
		self.url = '/api/model_runs/'

	def test_nonmember_user_fails(self):

		# first, just double check that running it without authentication fails
		response = self.client.post(self.url, self.test_request_data, format="json")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

		# new user has no permissions, but is authenticated
		new_user = User()
		new_user.save()
		self.client.force_authenticate(user=new_user)  # set the authentication - no tokens needed

		response = self.client.post(self.url, self.test_request_data, format="json")
		# should be getting a PermissionError because user isn't in the right group
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_nonmember_user_cant_delete(self):
		"""
			Make sure that only members of the same organization as a model run
			can delete it
		:return:
		"""
		org_user = User(username="deletion_test1")
		org_user.save()
		org_user.groups.add(self.organization.group)
		org_user.save()

		self.model_area.organization = self.organization
		self.model_area.save()

		other_user = User(username="deletion_test2")
		other_user.save()

		# make a new model run
		self.client.force_authenticate(user=org_user)  # set the authentication - no tokens needed
		response = self.client.post(self.url, self.test_request_data, format="json")
		# we're not testing model creation here, but we can't proceed if this isn't created, so test it
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		# now switch back to the one with no permissions
		self.client.force_authenticate(user=other_user)
		model_run_url = self.url + str(response.data["id"]) + "/"
		response = self.client.delete(model_run_url)
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

		# create another org and add other_user to it to make sure that being in *any* org isn't sufficient
		org2 = models.Organization(name="deletion_test")
		org2.save()
		other_user.groups.add(org2.group)
		self.client.force_authenticate(user=other_user)
		response = self.client.delete(model_run_url)
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

		# now delete from the user who should have permissions.
		self.client.force_authenticate(user=org_user)
		response = self.client.delete(model_run_url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

	def test_member_calibration_set_fails(self):
		# new user is now a group member
		new_user = User(username="test1")
		new_user.save()
		new_user.groups.add(self.organization.group)
		new_user.save()

		self.model_area.organization = None
		self.model_area.save()

		self.client.force_authenticate(user=new_user)  # set the authentication - no tokens needed

		response = self.client.post(self.url, self.test_request_data, format="json")
		# should be getting a PermissionError because calibration set isn't in an organization the user is a part of
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

		# make the calibration set happen within this organization
		self.model_area.organization = self.organization
		self.model_area.save()

		self.client.force_authenticate(user=new_user)  # set the authentication - no tokens needed
		response = self.client.post(self.url, self.test_request_data, format="json")
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		# now make sure that a new user that's not in the organization can't access the new resource
		new_user2 = User(username="test2")
		new_user2.save()
		self.client.force_authenticate(user=new_user2)  # set the authentication - no tokens needed
		response = self.client.get(f"{self.url}/{response.data['id']}")
		# it'll be forbidden if our queryset shows the item at all, but 404 if the queryset
		# excludes it.
		self.assertIn(response.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

	# test that user that's not a member of the group gets PermissionDenied
	# test that use of calibration set that's not in org gets PermissionDenied
	# test that use of calibration set and user in org succeeds and returns HTTP 200 and a status message
	# test that patching an existing item has same behavior