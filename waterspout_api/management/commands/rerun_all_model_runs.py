import logging
import time
import traceback

from django.core.management.base import BaseCommand, CommandError

from waterspout_api import models


log = logging.getLogger("waterspout")


class Command(BaseCommand):
	help = 'Sets all model runs to be re-run. Just sets their "complete" status to False and then the run processor will handle running them'

	def handle(self, *args, **options):
		models.ModelRun.objects.all().update(complete=False, running=False)
		log.info("All model runs set to incomplete")
