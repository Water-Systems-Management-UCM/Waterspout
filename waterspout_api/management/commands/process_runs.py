import logging
import time

from django.core.management.base import BaseCommand, CommandError

from waterspout_api import models
from Waterspout import settings


log = logging.getLogger("waterspout_service_run_processor")


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

				run.run()

	def _get_runs(self):
		log.debug("Checking for new model runs")
		new_runs = models.ModelRun.objects.filter(ready=True, running=False, complete=False)\
											.order_by('date_submitted')
		self._waiting_runs = new_runs