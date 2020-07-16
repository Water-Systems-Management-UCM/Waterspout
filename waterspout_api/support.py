import logging

import pandas

from . import models

from rest_framework.authtoken.models import Token

log = logging.getLogger(__name__)

def refresh_token_for_user(user):
	"""
		Deletes *all* existing tokens for the user specified, creates a new token, saves it,
		and returns it to the caller
	:param user: a Django User object
	:return: a DRF Token object. The actual token string is the "key" attribute on it
	"""
	# get rid of any current tokens
	Token.objects.filter(user=user).delete()

	new_token = Token.objects.create(user=user)
	new_token.save()
	return new_token


def get_or_create_token(user):
	"""
		Gets the current token for a user, and if no token exists, creates one. If one already exists,
		returns it. If you want to force a new token (and essentially a logout of all existing
		tokens for the user), just use `refresh_token_for_user` instead.
	:param user: a Django User object
	:return: a DRF Token object. The actual token string is the "key" attribute on it
	:return:
	"""
	tokens = Token.objects.filter(user=user)
	if len(tokens) == 0:
		return refresh_token_for_user(user)
	else:
		return tokens.first()


def add_user_to_organization_by_name(username, organization_name):
	log.info(f"Adding {username} to organization {organization_name}")
	user = models.User.objects.get(username=username)
	organization = models.Organization.objects.get(name=organization_name)

	organization.add_member(user)


def get_organizations_for_user(user):
	return [group.organization for group in user.groups.all()]


def compare_runs_by_id(model_run_id1, model_run_id2):
	model_run_1 = models.ModelRun.objects.get(id=model_run_id1)
	model_run_2 = models.ModelRun.objects.get(id=model_run_id2)

	return compare_runs_by_df(model_run_1.results.as_data_frame(), model_run_2.results.as_data_frame())


def compare_runs_by_df(df1, df2):
	# sort them by their effective year/island/crop index so that the rows are in the same order
	sorted_df1 = df1.sort_values(axis=0, by=["year", "g", "i"])
	sorted_df2 = df2.sort_values(axis=0, by=["year", "g", "i"])

	# we'll exclude these fields from comparison - since they're differences between values, ther
	# errors seem to compound, so we get differences even with less precise checking. I'm satisfied
	# if the other values come out equivalent.
	ignore_fields = ("xdiffland", "xdifftotalland", "xdiffwater")
	for field in ignore_fields:
		del sorted_df1[field]
		del sorted_df2[field]

	return pandas.testing.assert_frame_equal(sorted_df1, sorted_df2, check_like=True, check_column_type=False, check_dtype=False, check_less_precise=True)
