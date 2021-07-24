import logging

from django.core.management.base import BaseCommand

from waterspout_api import models

log = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Creates a user and adds them to all organizations that exist'

	def add_arguments(self, parser):
		parser.add_argument('--username', type=str, dest="username", required=True,)

	def handle(self, *args, **options):

		# create the user
		user = models.User.objects.create(username=options["username"])
		# add them to all existing organizations - this isn't wonderful in most
		# cases, but for an autologin user, we can assume that they should have
		# access to any orgs that have been created by now since the application
		# won't be able to be logged into normally after that.
		for org in models.Organization.objects.all():
			org.add_member(user)
