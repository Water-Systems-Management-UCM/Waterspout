import os

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User

import pandas

# Create your tests here.
from waterspout_api.load import dap
from waterspout_api import models, support
from . import TEST_DATA_FOLDER

import logging
log = logging.getLogger(__name__)

class ModelResultsTest(TransactionTestCase):  # Need to have a TransactionTestCase or the DAP load causes an IntegrityError
											# See https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom#23326971
	def setUp(self):
		"""
			Django tests start with an empty database, so we need to populate it
		:return:
		"""
		dap.load_dap()
		initial_calibration = models.CalibrationSet.objects.first()
		org = models.Organization.objects.first()

		user = User()
		user.save()

		self.model_run = models.ModelRun(
			organization=org,
			calibration_set=initial_calibration,
			user=user,
			ready=True
		)
		self.model_run.save()

		# add the default region and crop modifications
		models.RegionModification(model_run=self.model_run).save()
		models.CropModification(model_run=self.model_run, min_land_area_proportion=0).save()

	def test_final_results_are_correct(self):
		"""
			This test might need updating as the model changes, but for now, it's an
			important measure that in our translations of data from the web into the
			model and back out again, that we don't accidentally shuffle anything.
		:return:
		"""

		self.model_run.run()

		actual_results = pandas.read_csv(os.path.join(TEST_DATA_FOLDER, "DAP_v3_results.csv"))
		calculated_results = self.model_run.results.first().as_data_frame()

		# commented out for CD use where it was failing - useful for debug when run manually though
		#os.makedirs(os.path.join(os.path.join(TEST_DATA_FOLDER, "results")))  # make sure the results folder exists
		#calculated_results.to_csv(os.path.join(TEST_DATA_FOLDER, "results", "calculated_results.csv"))

		# assert_frame_equal returns None if two DFs are effectively equal
		# compare them to 2 decimal places - ignore data type differences since some is inferred from CSV
		self.assertIsNone(support.compare_runs(actual_results, calculated_results, compare_digits=3, keep_fields=["xland", "xwater", "xlandsc", "xwatersc"]), None)

	def test_no_infeasibilities_with_single_crop_modification(self):

		# add a crop modification to the model run - don't actually change anything, just
		# add one - in live testing there was an issue with this now
		a_crop = models.Crop.objects.first()  # get a crop
		log.info(a_crop.name)
		models.CropModification(model_run=self.model_run, crop=a_crop, min_land_area_proportion=0).save()

		self.model_run.run()

		actual_results = pandas.read_csv(os.path.join(TEST_DATA_FOLDER, "DAP_v3_results.csv"))
		calculated_results = self.model_run.results.first().as_data_frame()

		# commented out for CD use where it was failing - useful for debug when run manually though
		# os.makedirs(os.path.join(os.path.join(TEST_DATA_FOLDER, "results")))  # make sure the results folder exists
		# calculated_results.to_csv(os.path.join(TEST_DATA_FOLDER, "results", "calculated_results.csv"))

		# assert_frame_equal returns None if two DFs are effectively equal
		# compare them to 2 decimal places - ignore data type differences since some is inferred from CSV
		self.assertIsNone(support.compare_runs(actual_results, calculated_results, compare_digits=3,
		                                       keep_fields=["xland", "xwater", "xlandsc", "xwatersc"]), None)

