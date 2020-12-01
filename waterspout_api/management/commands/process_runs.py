import logging
import time
import traceback

from django.db import connection
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, RowRange, Window
from django.db.models.functions import Rank, ExtractYear

from waterspout_api import models
from Waterspout import settings


log = logging.getLogger("waterspout_service_run_processor")


class Command(BaseCommand):
	help = 'Starts the event loop that processes model runs and sends the commands to Mantis'

	def handle(self, *args, **options):
		self._waiting_runs = []
		self.process_runs()

	def process_runs(self):
		try:
			while True:
				self._get_runs()

				if len(self._waiting_runs) == 0:  # if we don't have any runs, go to sleep for a few seconds, then check again
					time.sleep(settings.MODEL_RUN_CHECK_INTERVAL)  # defaults to 4
					continue

				for run in self._waiting_runs:
					log.info(f"Running model run {run.id}")

					run.run()
		except:
			log.error(traceback.format_exc())
			if settings.DEBUG:  # if we're in production, don't raise the error, we'll get it in email
				raise

	def _get_runs(self):
		log.debug("Checking for new model runs")

		if "sqlite3" not in connection.settings_dict["ENGINE"]:  # window functions in django don't work on sqlite

			# the window function is used to ensure fairness, providing the ability to merge someone's newer runs with
			# someone else's older runs if the first person has lots of runs. Prevents someone from monopolizing the
			# run processor with API calls - instead, new people
			window_func = Window(
				expression=Rank('date_submitted'),
				partition_by=F('user_id'),
				output_field=F('rank'),
				order_by=F('date_submitted').asc(),
			),

			new_runs = models.ModelRun.objects.filter(ready=True, running=False, complete=False).annotate(window_func)\
												.order_by('rank')[:8]  # only select up to 8 at a time so that if someone
																	# submits a bunch over the API, we pause long enough to get new ones again soon
		else:
			new_runs = models.ModelRun.objects.filter(ready=True, running=False, complete=False) \
				.order_by('date_submitted')

		self._waiting_runs = new_runs