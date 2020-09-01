import logging

from django.core.management.base import BaseCommand

from waterspout_api import load

log = logging.getLogger("__name__")

class Command(BaseCommand):
	help = 'Loads default data into the database. Currently loads data for the DAP model'

	def add_arguments(self, parser):
		parser.add_argument('--region', nargs='+', type=str, dest="region", default=False,)

	def handle(self, *args, **options):
		log.info("Loading data to database")

		region_name = options["region"][0]
		log.info(f"Region {region_name}")

		region_module = getattr(load, region_name)
		loader_name = f"load_{region_name}"
		loader = getattr(region_module, loader_name)
		loader()
