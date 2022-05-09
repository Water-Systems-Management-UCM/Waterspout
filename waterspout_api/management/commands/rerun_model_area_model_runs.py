import logging
import time
import traceback

from django.core.management.base import BaseCommand, CommandError

from waterspout_api import models


log = logging.getLogger("waterspout")


class Command(BaseCommand):
	help = 'Sets all model runs in a single model area to be re-run. Just sets their "complete" status to False and then the run processor will handle running them'

	def add_arguments(self, parser):
		parser.add_argument('--model_area_name', type=str, dest="model_area_name", default=None,)

	def handle(self, *args, **options):
		if 'model_area_name' not in options or options['model_area_name'] is None:
			log.error("No model area to process. Please provide a --model_area_name parameter")

		model_area = models.ModelArea.objects.get(name=options['model_area_name'])
		for calibration_set in model_area.calibration_data.all():
			calibration_set.model_runs.update(complete=False, running=False)

		log.info(f"All model runs in area {options['model_area_name']} set to incomplete")
