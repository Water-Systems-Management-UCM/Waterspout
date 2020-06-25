import logging
import time

from django.core.management.base import BaseCommand, CommandError

from waterspout_api import models
from Waterspout import settings

from Dapper import calibration, scenarios

log = logging.getLogger("waterspout.commands.process_runs")


class Command(BaseCommand):
	help = 'Starts the event loop that processes model runs and sends the commands to Mantis'

	def handle(self, *args, **options):
		self._waiting_runs = []
		self.process_runs()

	def process_runs(self):
		while True:
			self._get_runs()

			if len(self._waiting_runs) == 0:  # if we don't have any runs, go to sleep for a few seconds, then check again
				time.sleep(settings.MODEL_RUN_CHECK_INTERVAL)  # defaults to 4
				continue

			for run in self._waiting_runs:
				log.info(f"Running model run {run.id}")
				# initially, we won't support calibrating the data here - we'll
				# just use an initial calibration set and then make our modifications
				# before running the scenarios

				#calib = calibration.ModelCalibration(run.calbration_df)
				#calib.calibrate()

				run.running = True
				run.save()  # mark it as running and save it so the API updates the status
				try:
					scenario_runner = scenarios.Scenario(df=run.scenario_df)
					results = scenario_runner.run()

					# now we need to load the resulting df back into the DB
					self.load_records(results_df=results, model_run=run)

					run.complete = True
					log.info("Model run complete")
				finally:  # make sure to mark it as not running regardless of its status or if it crashes
					run.running = False
					run.save()

	def load_records(self, results_df, model_run):
		"""
			Given a set of model results, loads the results to the database
		:param results_df:
		:param model_run:
		:return:
		"""
		log.info(f"Loading results for model run {model_run.id}")
		result_set = models.ResultSet(model_run=model_run)
		result_set.save()
		for record in results_df.itertuples():  # returns named tuples
			result = models.Result(result_set=result_set)
			result.i = models.Crop.objects.get(crop_code=record.i, organization=model_run.organization)
			result.g = models.Region.objects.get(internal_id=record.g, model_area__organization=model_run.organization)
			for column in record._fields:  # _fields isn't private - it's just preventing conflicts - see namedtuple docs
				if column in ("g", "i", "calibration_set"):
					continue
				setattr(result, column, getattr(record, column))
			result.save()

	def _get_runs(self):
		log.debug("Checking for new model runs")
		new_runs = models.ModelRun.objects.filter(ready=True, running=False, complete=False)\
											.order_by('date_submitted')
		self._waiting_runs = new_runs