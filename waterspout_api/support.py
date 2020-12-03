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
	return [val for val in [getattr(group, "organization", None) for group in user.groups.all()] if val is not None]


def compare_runs(run1, run2, compare_digits=3, keep_fields=False):
	"""
		Compares two model runs using pandas comparison tools - excludes difference fields (they
		may have compounding errors. Returns None if they're the same and raises an error if they're
		different.

		This is a loose wrapper around pandas' built-in comparison tool that makes it apply to our
		situation. First, each run parameter can be 1) a ModelRun ID, 2) a ModelRun object instance,
		or 3) a Pandas DataFrame - they don't need to be the same type, so

		support.compare_runs(14,pandas.read_csv("C:/Users/dsx/CodeLocal/Waterspout/waterspout_api/tests/data/results/calculated_results.csv"))

		is a valid command that compares ModelRun ID 14's results with the data in the provided CSV.
	:param run1: See main description
	:param run2: See main description
	:param compare_digits: How many decimal places should they be compared to? Defaults to 3.
	:return:
	"""
	if type(run1) is int:
		run1 = models.ModelRun.objects.get(id=run1)
	if type(run2) is int:
		run2 = models.ModelRun.objects.get(id=run2)

	if isinstance(run1, models.ModelRun):
		run1 = run1.results.as_data_frame()
	if isinstance(run2, models.ModelRun):
		run2 = run2.results.as_data_frame()

	if not isinstance(run1, pandas.DataFrame) or not isinstance(run2, pandas.DataFrame):
		raise TypeError("Runs provided for comparison must be integer model run IDs, ModelRun instances, or Pandas DataFrames.")

	run1.year = 1
	run2.year = 1
	# sort them by their effective year/island/crop index so that the rows are in the same order
	sorted_df1 = run1.sort_values(axis=0, by=["year", "g", "i"])
	sorted_df2 = run2.sort_values(axis=0, by=["year", "g", "i"])

	# drop the indexes or else the sorting is for nothing
	sorted_df1.reset_index(drop=True, inplace=True)
	sorted_df2.reset_index(drop=True, inplace=True)

	# we'll exclude these fields from comparison - since they're differences between values, ther
	# errors seem to compound, so we get differences even with less precise checking. I'm satisfied
	# if the other values come out equivalent.
	if not keep_fields:
		ignore_fields = ("xdiffland", "xdifftotalland", "xdiffwater")
		for field in ignore_fields:
			del sorted_df1[field]
			del sorted_df2[field]
	else:
		# make sure g, i, and year are in keep_fields
		keep_fields = list(set(list(keep_fields) + ["g", "i", "year"]))
		sorted_df1 = sorted_df1[keep_fields]
		sorted_df2 = sorted_df2[keep_fields]

	return pandas.testing.assert_frame_equal(sorted_df1, sorted_df2, check_like=True, check_column_type=False, check_dtype=False, check_less_precise=compare_digits)
