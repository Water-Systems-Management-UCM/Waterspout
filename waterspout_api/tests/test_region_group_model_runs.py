import os
import json
import copy
import logging

from django.contrib.auth.models import User, Group

from rest_framework.test import APITestCase, APIRequestFactory, APITransactionTestCase
from rest_framework import status

from waterspout_api.load import dap
from waterspout_api import support, models
from . import TEST_DATA_FOLDER

log = logging.getLogger(__name__)

class APIModelRunTestCase(APITransactionTestCase):# Need to have a TransactionTestCase or the DAP load causes an IntegrityError
											# See https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom#23326971
	def setUp(self):
		"""
			Django tests start with an empty database, so we need to populate it
		:return:
		"""
		dap.load_dap()
		self.initial_calibration = models.CalibrationSet.objects.first()
		self.org = models.Organization.objects.first()

		# add a new user as an organization member so it can post model runs to the API
		user = User()
		user.save()
		self.org.add_member(user)

		south_delta_group = models.RegionGroup.objects.get(name="South Delta Water Agency")
		south_delta_group_members = list(south_delta_group.regions.all())  # we'll go through it a few times, so just pull the whole thing

		adjusted_by_group_model_run_creation = json.loads("""
		{
                                "name": "South Delta Water Agency 50% via group",
                                "description": null,
                                "ready": true,
                                "organization": 2,
                                "calibration_set": 2,
                                "rainfall_set": null,
                                "region_modifications": [{"region":null,"land_proportion":1,"water_proportion":1,"rainfall_proportion":1},{"water_proportion":0.5,"rainfall_proportion":1,"land_proportion":1,"modeled_type":0,"region_group":0}],
                                "crop_modifications": [{"crop":null,"price_proportion":1,"yield_proportion":1,"min_land_area_proportion":0,"max_land_area_proportion":null}]
                            }
		""")
		adjusted_by_group_model_run_creation["organization"] = self.org.id
		adjusted_by_group_model_run_creation["calibration_set"] = self.initial_calibration.id

		# first item is where we just set the group settings and want to make sure
		# the settings get correctly applied to all regions
		# set the group item ID
		adjusted_by_group_model_run_creation["region_modifications"][-1]["region_group"] = south_delta_group.id

		# make the version that should match the group setting version,
		# but it's done by manually setting each individual region to the same value
		adjusted_by_region_model_run_creation = copy.deepcopy(adjusted_by_group_model_run_creation)
		adjusted_by_region_model_run_creation["region_modifications"].pop(1)  # get rid of the group item

		for member in south_delta_group_members:
			adjusted_by_region_model_run_creation["region_modifications"].append({"water_proportion":0.5,"rainfall_proportion":1,"land_proportion":1,"modeled_type":0,"region":member.id})

		# now make a version where we set the group setting, but then apply settings to individual regions as overrides
		# that completely undo the group settings
		adjusted_by_group_but_undone = copy.deepcopy(adjusted_by_group_model_run_creation)
		for member in south_delta_group_members:
			adjusted_by_group_but_undone["region_modifications"].append({"water_proportion":1,"rainfall_proportion":1,"land_proportion":1,"modeled_type":0,"region":member.id})

		# Now, when we run these, we'll run the code that generates the modifications for each one from groups and compare
		# the modifications to make sure they're the same, then, run the model and compare the outputs

		# now copy the group one and add a single override
		adjusted_by_group_with_overrides = copy.deepcopy(adjusted_by_group_model_run_creation)
		override_region = south_delta_group_members[1]
		adjusted_by_group_with_overrides["region_modifications"].append(
			{"water_proportion": 1.1, "rainfall_proportion": 1, "land_proportion": 1, "modeled_type": 0,
			 "region": override_region.id})

		# then copy the group one and change it's modeling type - we'll confirm that our output modifications all have that modeled type
		adjusted_with_changed_modeling_type = copy.deepcopy(adjusted_by_group_model_run_creation)
		adjusted_with_changed_modeling_type["region_modifications"][-1]["modeled_type"] = 1

		self.client.force_login(user)

		# create the model runs and store their IDs - we'll use these in individual tests
		self.model_run_ids = {}

		response = self.client.post('/api/model_runs/', adjusted_by_group_model_run_creation, format="json")
		self.model_run_ids["adjusted_by_group_model_run_creation"] = response.json()['id']
		response = self.client.post('/api/model_runs/', adjusted_by_region_model_run_creation, format="json")
		self.model_run_ids["adjusted_by_region_model_run_creation"] = response.json()['id']
		response = self.client.post('/api/model_runs/', adjusted_by_group_with_overrides, format="json")
		self.model_run_ids["adjusted_by_group_with_overrides"] = response.json()['id']
		response = self.client.post('/api/model_runs/', adjusted_with_changed_modeling_type, format="json")
		self.model_run_ids["adjusted_with_changed_modeling_type"] = response.json()['id']
		response = self.client.post('/api/model_runs/', adjusted_by_group_but_undone, format="json")
		self.model_run_ids["adjusted_by_group_but_undone"] = response.json()['id']

	def test_undone_region_modification(self):
		# get it by name because the transaction test case can roll back objects, but not ID sequences,
		# so it won't always be run 1
		base_case = models.ModelRun.objects.get(name="Base Case")
		base_case.run()
		base_case_results = base_case.results.first().as_data_frame()

		region_modified_undone = models.ModelRun.objects.get(
			pk=self.model_run_ids["adjusted_by_group_but_undone"])
		region_modified_undone.convert_region_group_modifications()  # make sure to have it convert them to individual modifications
		# Once converted, we can check that we don't end up with anything that took on the group settings
		for mod in region_modified_undone.region_modifications.all():
			if mod.region is None:  # skip the group modification that won't apply
				continue
			self.assertEqual(mod.water_proportion, 1)

		region_modified_undone.run()  # we don't really need to run it, but might as well
		region_modified_undone_results = region_modified_undone.results.first().as_data_frame()

		self.assertIsNone(support.compare_runs(base_case_results, region_modified_undone_results, compare_digits=3,
											   keep_fields=["xland", "xlandsc", "xwatersc"]), None)

	def test_compare_individual_region_with_group_run(self):
		"""
			Do we need to compare the actual modification objects are the same, or is comparing the results sufficient?
			If this becomes too slow, then we can switch to comparing the inputs instead of the outputs, but that's
			potentially risky if the inputs change and we don't detect an output modification.
		:return:
		"""
		# run this one before proceeding because we're going to compare all the others with it
		group_run = models.ModelRun.objects.get(pk=self.model_run_ids["adjusted_by_group_model_run_creation"])
		group_run.run()

		region_modified_version = models.ModelRun.objects.get(pk=self.model_run_ids["adjusted_by_region_model_run_creation"])
		region_modified_version.run()
		region_modified_results = region_modified_version.results.first().as_data_frame()

		group_modified_version = models.ModelRun.objects.get(pk=self.model_run_ids["adjusted_by_group_model_run_creation"])
		group_modified_results = group_modified_version.results.first().as_data_frame()

		# assert_frame_equal returns None if two DFs are effectively equal
		# compare them to 2 decimal places - ignore data type differences since some is inferred from CSV
		self.assertIsNone(support.compare_runs(group_modified_results, region_modified_results, compare_digits=3,
		                                       keep_fields=["xland", "xlandsc", "xwatersc"]), None)

	def test_compare_version_with_overrides(self):
		# run this one before proceeding because we're going to compare all the others with it
		group_run = models.ModelRun.objects.get(pk=self.model_run_ids["adjusted_by_group_model_run_creation"])
		group_run.run()

		region_override_version = models.ModelRun.objects.get(pk=self.model_run_ids["adjusted_by_group_with_overrides"])
		region_override_version.run()
		region_modified_results = region_override_version.results.first().as_data_frame()

		group_modified_version = models.ModelRun.objects.get(pk=self.model_run_ids["adjusted_by_group_model_run_creation"])
		group_modified_results = group_modified_version.results.first().as_data_frame()

		# need to check that it raises AssertionError because pandas's df checking tooling
		# is assert_frame_equal, and it raises an assertion if they aren't (and returns None otherwise, I believe)
		# so it raising an AssertionError is what we want here. It's possible it'd make sense for compare_runs
		# to catch this exception and do its own thing, but this is fine for now.
		self.assertRaises(AssertionError, support.compare_runs, group_modified_results, region_modified_results, compare_digits=3,
		                                       keep_fields=["xland", "xlandsc", "xwatersc"])

	def test_changed_modeling_type(self):
		changed_model_type = models.ModelRun.objects.get(pk=self.model_run_ids["adjusted_with_changed_modeling_type"])
		changed_model_type.convert_region_group_modifications()

		for mod in changed_model_type.region_modifications.filter(region__isnull=False, region_group__isnull=False):
			self.assertEqual(mod.modeled_type, 1)

		changed_model_type.run()

	def test_changed_modeling_type_to_zero(self):
		adjusted_modeling_type = json.loads("""
														{
												                                "name": "South Delta Water Agency 50% via group",
												                                "description": null,
												                                "ready": true,
												                                "organization": 2,
												                                "calibration_set": 2,
												                                "rainfall_set": null,
												                                "region_modifications": [{"region":null,"land_proportion":1,"water_proportion":1,"rainfall_proportion":1}],
												                                "crop_modifications": [{"crop":null,"price_proportion":1,"yield_proportion":1,"min_land_area_proportion":0,"max_land_area_proportion":null}]
												                            }
														""")
		adjusted_modeling_type["organization"] = self.org.id
		adjusted_modeling_type["calibration_set"] = self.initial_calibration.id

		# set all groups to REMOVED
		for group in models.RegionGroup.objects.all():
			adjusted_modeling_type["region_modifications"].append(
				{"water_proportion": 1, "rainfall_proportion": 1, "land_proportion": 1, "modeled_type": models.Region.REMOVED, "region_group": group.id}
			)

		response = self.client.post('/api/model_runs/', adjusted_modeling_type, format="json")
		model_run_id = response.json()['id']
		model_run = models.ModelRun.objects.get(pk=model_run_id)

		model_run.run()
		model_run_results = model_run.results.first().as_data_frame()
		self.assertEqual(model_run_results.size, 0)  # this model run should basically cause all regions to be dropped, so result should be empty




