import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from waterspout_api import models

log = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Creates or resets a superuser for local development and adds it to every organization. Only runs with DEBUG on'

	def add_arguments(self, parser):
		parser.add_argument('--username', type=str, dest="username", default="dev",)
		parser.add_argument('--password', type=str, dest="password", default="dev",)

	def handle(self, *args, **options):
		if not settings.DEBUG:  # this account has a known password, so it must never be created on a real server
			raise CommandError("create_dev_user only runs with DEBUG on, because it creates an account with a known password")

		user, created = models.User.objects.get_or_create(username=options["username"])
		user.set_password(options["password"])
		user.is_active = True
		user.is_staff = True
		user.is_superuser = True
		user.save()

		# the app shows the model areas of the user's organizations, so put the dev user in all of them
		organizations = [org for org in models.Organization.objects.all() if org.group is not None]
		for org in organizations:
			if not org.has_member(user):
				org.add_member(user)

		self.stdout.write(f"{'Created' if created else 'Reset'} dev user - username: {user.username}, password: {options['password']}, "
						  f"superuser in {len(organizations)} organizations")
