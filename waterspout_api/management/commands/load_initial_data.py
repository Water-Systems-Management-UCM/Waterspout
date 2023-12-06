import logging

from django.core.management.base import BaseCommand

from waterspout_api import load

log = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Loads default data into the database. Provide the region name to load (dap, agwa, ca_cv) as the --region argument'

	def add_arguments(self, parser):
		parser.add_argument('--area', nargs='+', type=str, dest="area", default=None,)

	def handle(self, *args, **options):
		log.info("Loading data to database")

		if not options["area"] or not options["area"][0] or options["area"][0] == "":
			raise ValueError("Can't proceed - no area name to load")

		area_name = options["area"][0]
		log.info(f"Area {area_name}")

		area_module = getattr(load, area_name)
		loader_name = f"load_{area_name}"
		loader = getattr(area_module, loader_name)
		loader()
