from io import StringIO

from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from waterspout_api import models


class CreateDevUserTestCase(TestCase):

	def setUp(self):
		self.organization = models.Organization.objects.create(name="dev user test org", group=Group.objects.create(name="dev user test org"))

	@override_settings(DEBUG=False)
	def test_refuses_without_debug(self):
		with self.assertRaises(CommandError):
			call_command("create_dev_user")
		self.assertFalse(User.objects.filter(username="dev").exists())

	@override_settings(DEBUG=True)
	def test_creates_and_resets_superuser(self):
		call_command("create_dev_user", stdout=StringIO())
		user = User.objects.get(username="dev")
		user.set_password("changed")
		user.save()

		call_command("create_dev_user", stdout=StringIO())  # running it again resets the account instead of failing
		user = User.objects.get(username="dev")
		self.assertTrue(user.is_superuser and user.is_staff and user.is_active)
		self.assertTrue(user.check_password("dev"))
		self.assertTrue(self.organization.has_member(user))
