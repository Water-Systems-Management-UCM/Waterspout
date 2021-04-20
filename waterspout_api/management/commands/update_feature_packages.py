import logging
import time
import traceback

from django.core.management.base import BaseCommand, CommandError

from waterspout_api import feature_packages

log = logging.getLogger("waterspout")


class Command(BaseCommand):
	help = 'Updates all model area feature packages based on any core code/feature updates'

	def handle(self, *args, **options):
		feature_packages.update_all_feature_packages()
		log.info("All feature packages updated")
