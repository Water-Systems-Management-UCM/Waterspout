import logging

from django.core.management.base import BaseCommand

from waterspout_api.load import dap

log = logging.getLogger("__name__")

class Command(BaseCommand):
	help = 'Loads default data into the database. Currently loads data for the DAP model'

	def handle(self, *args, **options):
		dap.load_dap()