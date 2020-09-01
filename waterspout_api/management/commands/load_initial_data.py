import logging

from django.core.management.base import BaseCommand

from waterspout_api import load

log = logging.getLogger("__name__")


class Command(BaseCommand):
	help = 'Loads default data into the database. Provide the region name to load (dap, agwa) as the --region argument'

	def add_arguments(self, parser):
		parser.add_argument('--region', nargs='+', type=str, dest="region", default=None,)

	def handle(self, *args, **options):
		log.info("Loading data to database")

		if not options["region"] or not options["region"][0] or options["region"][0] == "":
			raise ValueError("Can't proceed - no region name to load")

		region_name = options["region"][0]
		log.info(f"Region {region_name}")

		region_module = getattr(load, region_name)
		loader_name = f"load_{region_name}"
		loader = getattr(region_module, loader_name)
		loader()
