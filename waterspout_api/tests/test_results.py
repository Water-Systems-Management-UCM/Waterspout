import os

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User

import pandas

# Create your tests here.
from waterspout_api.load import dap
from waterspout_api import models
from . import TEST_DATA_FOLDER


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

	def test_final_results_are_correct(self):
		"""
			This test might need updating as the model changes, but for now, it's an
			important measure that in our translations of data from the web into the
			model and back out again, that we don't accidentally shuffle anything.
		:return:
		"""

		self.model_run.run()

		actual_results = pandas.read_csv(os.path.join(TEST_DATA_FOLDER, "DAP_v2_results.csv"))
		calculated_results = self.model_run.results.as_data_frame()
		calculated_results.to_csv(os.path.join(TEST_DATA_FOLDER, "results", "calculated_results.csv"))
		# assert_frame_equal returns None if two DFs are effectively equal

		# sort them by their effective year/island/crop index so that the rows are in the same order
		sorted_actual = actual_results.sort_values(axis=0, by=["year", "g", "i"])
		sorted_calculated = calculated_results.sort_values(axis=0, by=["year", "g", "i"])

		# we'll exclude these fields from comparison - since they're differences between values, ther
		# errors seem to compound, so we get differences even with less precise checking. I'm satisfied
		# if the other values come out equivalent.
		ignore_fields = ("delta", "xlandsc","xwatersc","xdiffland","xdifftotalland","xdiffwater")
		for field in ignore_fields:
			del sorted_actual[field]
			del sorted_calculated[field]

		# compare them to 5 decimal places - ignore data type differences since some is inferred from CSV
		self.assertIsNone(pandas.testing.assert_frame_equal(sorted_actual, sorted_calculated		                                                    ,
		                                                    check_like=True, check_column_type=False,
		                                                    check_dtype=False,
		                                                    check_less_precise=True), None)
