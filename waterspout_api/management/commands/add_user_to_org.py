import logging

from django.core.management.base import BaseCommand

from waterspout_api.support import add_user_to_organization_by_name

log = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Adds a user to an organization, giving them permission to work in that organization\'s model areas'

	def add_arguments(self, parser):
		parser.add_argument('--user', nargs='+', type=str, dest="username", default=False,)
		parser.add_argument('--organization', nargs='+', type=str, dest="organization_name", default=False,)

	def handle(self, *args, **options):
		add_user_to_organization_by_name(username=options["username"][0], organization_name=options["organization_name"][0])
