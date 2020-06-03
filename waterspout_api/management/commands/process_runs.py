import logging
import time

from django.core.management.base import BaseCommand, CommandError

from npsat_manager import mantis_manager, models

log = logging.getLogger("npsat_manager.commands.process_runs")


class Command(BaseCommand):
	help = 'Starts the event loop that processes model runs and sends the commands to Mantis'

	def handle(self, *args, **options):
		mantis_servers = mantis_manager.initialize()
		# asyncio.run(mantis_manager.main_model_run_loop(mantis_servers))  # see note on main_model_run_loop for why we're not using it

		self._waiting_runs = []
		self.mantis_server = mantis_servers[0]  # leaving in place the infra for multiple servers in the future, but we'll use one for now

		self.process_runs()

	def process_runs(self):
		while True:
			self._get_runs()

			if len(self._waiting_runs) == 0:  # if we don't have any runs, go to sleep for a few seconds, then check again
				time.sleep(2)
				continue

			for run in self._waiting_runs:
				self.mantis_server.send_command(model_run=run)

	def _get_runs(self):
		new_runs = models.ModelRun.objects.filter(ready=True, running=False, complete=False)\
											.order_by('date_submitted')\
											.prefetch_related('modifications')  # get runs that aren't complete
		self._waiting_runs = new_runs
