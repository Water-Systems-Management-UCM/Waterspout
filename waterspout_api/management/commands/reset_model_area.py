import logging

from django.core.management.base import BaseCommand

from waterspout_api.models import ModelArea
from waterspout_api.load.core import reset_organization_for_reload

log = logging.getLogger("__name__")


class Command(BaseCommand):
	help = 'Removes an existing model area and replaces it, keeping the same user access and permissions.' \
	       'Loads all its default data into the database anew. Provide the region name to load (dap, agwa) as the --region argument'

	def add_arguments(self, parser):
		parser.add_argument('--model_area_id', nargs='+', type=str, dest="model_area_id", default=None,)
		parser.add_argument('--area', nargs='+', type=str, dest="area", default=None,)

	def handle(self, *args, **options):
		log.info("Removing and recreating model area")

		if not options["area"] or not options["area"][0] or options["area"][0] == "":
			raise ValueError("Can't proceed - no area name to load")

		if not options["model_area_id"] or not options["model_area_id"][0] or options["model_area_id"][0] == "":
			raise ValueError("Can't proceed - no model area to remove")

		area_name = options["area"][0]
		log.info(f"Area {area_name}")

		model_area_id = options["model_area_id"][0]
		log.info(f"Model Area ID {model_area_id}")

		model_area = ModelArea.objects.get(id=int(model_area_id))
		log.info(model_area.name)

		reset_organization_for_reload(model_area, area_name)
