"""
	Given the ID of an existing model area and a multipliers CSV, deletes the
	model area's current multipliers and loads the CSV in their place. Model runs
	don't need to rerun - the multipliers are applied when results are displayed
"""

import logging
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from waterspout_api.load.core import load_multipliers
from waterspout_api import models

from Waterspout.settings import BASE_DIR

log = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Replaces all multipliers for a model area with the ones in a CSV. Relative paths are read from waterspout_api/data'

	def add_arguments(self, parser):
		parser.add_argument('--model_area_id', type=int, dest="model_area_id", required=True)
		parser.add_argument('--multipliers_file', type=str, dest="multipliers_file", required=True)

	def handle(self, *args, **options):
		model_area = models.ModelArea.objects.get(id=options["model_area_id"])
		multipliers_file = os.path.join(BASE_DIR, "waterspout_api", "data", options["multipliers_file"])  # absolute paths are kept as they are
		log.info(f"Replacing multipliers for model area {model_area.id} ({model_area.name}) with {multipliers_file}")

		area_multipliers = models.EmploymentMultipliers.objects.filter(region__model_area=model_area)
		with transaction.atomic():  # if any row fails to load, keep the old multipliers
			deleted, _ = area_multipliers.delete()
			load_multipliers(multipliers_file, model_area)

		log.info(f"Deleted {deleted} multipliers and loaded {area_multipliers.count()}")
