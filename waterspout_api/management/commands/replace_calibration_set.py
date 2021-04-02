"""
	Given the ID of an existing calibration set and a new
	CSV file, adds the new CSV file as a calibration set
	to the same model area
	as the first calibration set, updates all existing model
	runs to use the new calibration set, deletes the old
	calibration set, and invalidates all model runs so they
	get reprocessed
"""

import logging

from django.core.management.base import BaseCommand

from waterspout_api.load.core import load_input_data_set
from waterspout_api import models

log = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Loads a new calibration set, deletes the old one specified, and reruns model runs with new calibration data'

	def add_arguments(self, parser):
		parser.add_argument('--calib_set_id', nargs='+', type=int, dest="calib_set_id")
		parser.add_argument('--new_data', nargs='+', type=str, dest="new_data_csv")
		parser.add_argument('--years', nargs='+', type=str, dest="years")

	def handle(self, *args, **options):
		years = options["years"][0].split(",")
		log.info(years)

		# 1 get the existing calibration set and its model area
		calib_set_id = int(options["calib_set_id"][0])
		calibration_set = models.CalibrationSet.objects.get(id=calib_set_id)
		model_area = calibration_set.model_area

		# 2 load the new calibration set to the same model area
		log.info("Loading new calibration set")
		csv_file = options["new_data_csv"][0]
		new_calibration_set = load_input_data_set(csv_file, model_area=model_area, years=years,
		                    set_model=models.CalibrationSet,
		                    item_model=models.CalibratedParameter,
		                    set_lookup="calibration_set"
							)

		# 3 update existing model runs to use the new calibration set
		# and 5 force a rerun of all existing model runs
		log.info("Setting new calibration set on model runs and scheduling model runs to rerun")
		models.ModelRun.objects.all().update(calibration_set=new_calibration_set,
		                                     complete=False,
		                                     running=False)

		# 4 delete the old calibration set
		log.info("Deleting the old calibration set")
		calibration_set.delete()
