import logging
import traceback
import decimal
import json

import numpy

import django
from django.db import models  # we're going to geodjango this one - might not need it, but could make some things nicer
from django.db.models import Q
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
User = get_user_model()  # define user by this method rather than direct import - safer for the future

from guardian.shortcuts import assign_perm
from django.db.models.signals import post_save
from django.dispatch import receiver


from Waterspout import settings

import pandas
from Dapper import scenarios, get_version as get_dapper_version

log = logging.getLogger("waterspout.models")


class SimpleJSONField(models.TextField):
	"""
		converts dicts to JSON strings on save and converts JSON to dicts
		on load
	"""

	def get_prep_value(self, value):
		return json.dumps(value)

	def from_db_value(self, value, expression, connection):
		return json.loads(value)


class UserProfile(models.Model):
	"""
		Basically just for user settings
	"""

	user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)

	_serializer_fields = ["id", "user", "show_organization_model_runs", "show_organization_model_runs_tooltip"]
	# basic settings
	show_organization_model_runs = models.BooleanField(default=True)
	show_organization_model_runs_tooltip = "By default, the application shows all model runs from within your organization" \
	                                       " and gives you the option to temporarily show only your model runs." \
	                                       " This setting changes that behavior so that, by default, you only see model runs" \
	                                       " that you created yourself and then you can temporarily change the listing to" \
	                                       " see all model runs in your organization."


# set up the signal receivers that get triggered after a user is created so that everyone has a userprofile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		new_profile = UserProfile.objects.create(user=instance)
		assign_perm("change_userprofile", instance, new_profile)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
	instance.profile.save()


class Organization(models.Model):
	"""
		Since this application is designed to support multiple models, possibly in the same instance, make most things
		be ties to an "organization" of some kind - we'll include users in the organization and arrange permissions
		around users within the organization.

		We could have made this a subclass of the Group object, but then reverse relationships may not work correctly.
		Instead we'll just
	"""
	name = models.CharField(max_length=255, null=False, blank=False)

	# TODO: This shouldn't allow nulls or blanks in the future
	group = models.OneToOneField(Group, on_delete=models.DO_NOTHING, null=True, blank=True)

	def has_member(self, user):
		return self.group in user.groups.all()  # True if this group is in that set, otherwise, False

	def add_member(self, user):
		self.group.user_set.add(user)
		self.group.save()

	def __str__(self):
		return f"Organization: {self.name}"


class ModelArea(models.Model):
	"""
		This would be something like "The Delta", or "Washington" - mostly, this will be one to one with organizations,
		but just in case we want to be able to deploy multiple models for an organization in the future, we'll store it
		this way.
	"""
	organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name="model_areas")
	name = models.CharField(max_length=255, unique=True)

	data_folder = models.CharField(max_length=255, default="dap")  # which folder did the data for this come from during loading? Can
													# help us if we want to update some data later

	description = models.TextField(null=True, blank=True)
	# preferences reverse 1 to 1

	map_center_latitude = models.DecimalField(max_digits=4, decimal_places=2)
	map_center_longitude = models.DecimalField(max_digits=5, decimal_places=2)
	map_default_zoom = models.SmallIntegerField()

	# these values define the ranges available when creating a model run in this region
	min_water = models.PositiveSmallIntegerField(default=50)
	max_water = models.PositiveSmallIntegerField(default=120)
	min_rainfall = models.PositiveSmallIntegerField(default=10)
	max_rainfall = models.PositiveSmallIntegerField(default=200)
	min_land = models.PositiveSmallIntegerField(default=50)
	max_land = models.PositiveSmallIntegerField(default=100)
	min_price = models.PositiveSmallIntegerField(default=80)
	max_price = models.PositiveSmallIntegerField(default=120)
	min_yield = models.PositiveSmallIntegerField(default=80)
	max_yield = models.PositiveSmallIntegerField(default=120)
	min_crop_area = models.PositiveSmallIntegerField(default=0)
	max_crop_area = models.PositiveSmallIntegerField(default=200)

	main_help_page_content = models.TextField(null=True, blank=True)

	feature_package_name = models.CharField(max_length=100, default="DEFAULT")

	def __str__(self):
		return self.name

	@property
	def model_defaults(self):
		# Just making it a dict so that it comes out of the serializer grouped
		return {
			"min_water": self.min_water,
			"max_water": self.max_water,
			"min_rainfall": self.min_rainfall,
			"max_rainfall": self.max_rainfall,
			"min_land": self.min_land,
			"max_land": self.max_land,
			"min_price": self.min_price,
			"max_price": self.max_price,
			"min_yield": self.min_yield,
			"max_yield": self.max_yield,
			"min_crop_area": self.min_crop_area,
			"max_crop_area": self.max_crop_area,
		}

	# elasticities code commented out because we don't run calibration
	# ourselves right now
	#@property
	#def elasticities_as_dict(self):
	#	return {item.crop.crop_code: float(item.value) for item in self.elasticities}

	@property
	def supports_rainfall(self):
		return self.region_set.filter(supports_rainfall=True).exists()
	@property
	def supports_irrigation(self):
		return self.region_set.filter(supports_irrigation=True).exists()


class ModelAreaPreferences(models.Model):
	"""
		This model is so that we can group preferences and features for model areas
		and keep them organized
	"""
	# prevent users from reducing price/yield below the value that would make profits negative
	# basically forces stormchaser to create cards for crops when All Crops
	# goes to negative profits for the crop
	enforce_price_yield_constraints = models.BooleanField(default=True)

	# if True, and the user makes an adjustment that would create
	# negative profits, it forces the slider they weren't using upward as they move the other
	# downward. If False, it's purely advisory
	lock_price_yield_ratio = models.BooleanField(default=False)

	# Should visualizations and downloads include net revenues for this model area? By default we
	# don't want to - in most cases, it won't be something we want people to see - but we'll want
	# it to be able to be accessed for debugging purposes
	include_net_revenue = models.BooleanField(default=False)

	# should region-linking of crops be enabled?
	region_linked_crops = models.BooleanField(default=False)

	# whether or not to show the ability to view model run creation code
	allow_model_run_creation_code_view = models.BooleanField(default=False)

	# flags to indicate an entire set of features in data visualization
	# where they can choose additional model runs for comparison,
	# can normalize to a base run, and can see worst case outcomes
	allow_viz_multiple_comparisons = models.BooleanField(default=False)
	allow_viz_normalization = models.BooleanField(default=False)
	allow_viz_region_filter = models.BooleanField(default=False)
	allow_viz_worst_case = models.BooleanField(default=False)

	allow_static_regions = models.BooleanField(default=False)
	allow_removed_regions = models.BooleanField(default=False)

	model_area = models.OneToOneField(ModelArea,
	                                  on_delete=models.CASCADE,
	                                  related_name="preferences"
	                                  )


# set up the signal receivers that get triggered after a model area is created so that everyone has a userprofile
@receiver(post_save, sender=ModelArea)
def create_model_area_preferences(sender, instance, created, **kwargs):
	if created:
		ModelAreaPreferences.objects.create(model_area=instance)

@receiver(post_save, sender=ModelArea)
def save_model_area(sender, instance, **kwargs):
	instance.preferences.save()


#class Elasticity(models.Model):
# elasticities code commented out because we don't run calibration
# ourselves right now
#	"""
#		We store elasticities for Dapper as individual records here,
#		but we'll access them on the ModelArea object to send to Dapper
#	"""
#	model_area = models.ForeignKey(ModelArea, on_delete=models.CASCADE, related_name="elasticities")
#	crop = models.ForeignKey("Crop", on_delete=models.CASCADE, related_name="elasticities")
#	value = models.DecimalField(max_digits=6, decimal_places=4)


class RegionGroup(models.Model):
	name = models.CharField(max_length=255, null=False, blank=False)
	internal_id = models.CharField(max_length=100, null=False, blank=False)  # typically we have some kind of known ID to feed to a model that means something to people
	model_area = models.ForeignKey(ModelArea, on_delete=models.CASCADE)

	geometry = models.JSONField(null=True, blank=True)  # this will just store GeoJSON and then we'll combine into collections manually


class Region(models.Model):
	class Meta:
		unique_together = ['name', 'model_area']
		indexes = [
			models.Index(fields=("internal_id",)),
			models.Index(fields=("model_area_id", "supports_rainfall",)),  # we'll use these to set an attribute whenever someone loads a model area
			models.Index(fields=("model_area_id", "supports_irrigation",))
		]

	name = models.CharField(max_length=255, null=False, blank=False)
	internal_id = models.CharField(max_length=100, null=False, blank=False)  # typically we have some kind of known ID to feed to a model that means something to people
	external_id = models.CharField(max_length=100, null=True, blank=True)  # a common external identifier of some kind
	description = models.TextField(null=True, blank=True)
	# .extra_attributes reverse lookup

	geometry = models.JSONField(null=True, blank=True)  # this will just store GeoJSON and then we'll combine into collections manually

	model_area = models.ForeignKey(ModelArea, on_delete=models.CASCADE)
	group = models.ForeignKey(RegionGroup, null=True, blank=True, on_delete=models.CASCADE)  # there could be a reason to make it a many to many instead, but
																	# I can't think of a use case right now, and it'd require some PITA
																	# logic to tease apart specifications for regions in overlapping groups

	supports_rainfall = models.BooleanField(default=False)  # whether or not this region has any rainfall/dryland components
	supports_irrigation = models.BooleanField(default=True)  # whether or not this region has any irrigated components

	serializer_fields = ("id", "name", "internal_id", "description", "geometry", "model_area", "group",
	                     "supports_rainfall", "supports_irrigation", "multipliers")

	def __str__(self):
		return "Area {}: Region {}".format(self.model_area.name, self.name)


class RegionMultipliers(models.Model):
	region = models.OneToOneField(Region, on_delete=models.CASCADE, related_name="multipliers")

	total_revenue = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
	direct_value_add = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
	total_value_add = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
	direct_jobs = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
	total_jobs = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)


class RegionExtra(models.Model):
	"""
		Extra custom attributes that can be set per region instance, available by filtering
		`region.extra_attributes.filter(name == "{attribute_name}")`, for example.
	"""
	region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="extra_attributes")
	name = models.CharField(max_length=255, null=False, blank=False)
	value = models.TextField(null=True, blank=True)
	data_type = models.CharField(max_length=5)  # indicates the Python data type to cast it to if it's not a string


class Crop(models.Model):
	"""
		A single unit for individual crops - note that we need to pull crops by organization - the same crop could
		exist for multiple organizations. We don't want to load them in for all organizations because then we have to
		worry about if it means the same exact thing across organizations, and what do changes mean to each group, etc,
		etc. Let's keep it a known, manageable level of complex and assign crops to organizations even if it means
		duplicating crops between organizations.
	"""
	class Meta:
		unique_together = ['crop_code', 'model_area']
		indexes = [
			models.Index(fields=("name",))
		]

	name = models.CharField(max_length=255, null=False, blank=False)  # human readable crop name
	crop_code = models.CharField(max_length=30, null=False, blank=False)  # code used in the models (like ALFAL for Alfalfa)
	model_area = models.ForeignKey(ModelArea, on_delete=models.CASCADE)  # clear any crops for an org when deleted

	def __str__(self):
		return self.name


class CropGroup(models.Model):
	"""
		A unit to group individual crops together - note that we need to crop groups are also by organization and
		the same crop group exist for multiple organizations
	"""
	name = models.CharField(max_length=255, null=False, blank=False)
	crops = models.ManyToManyField(Crop)  # Each crop can be in many groups


class RecordSet(models.Model):
	class Meta:
		abstract = True
	"""
		For storing the results of calibration parameters that come out of phase 1 of the model - we'll load a few sets
		of calibrated parameters initially, but then provide a black box version of the calibration parameters. We can
		then have behavior that tries a lookup for a calibration set, and if it doesn't exist, runs the calibration.
	"""

	record_model_name = "ModelItem"
	years = models.TextField()  # yes, text. We'll concatenate text as a year lookup
	# prices = model

	def as_data_frame(self, exclude_regions=None):
		"""
			Returns the data frame that needs to be run through the model itself
			:param exclude_regions: list of region internal ids - regions in this list will not have their data
						included in the output data frame
		:return:
		"""
		# .values() makes a queryset into an iterable of dicts. Coerce that to a list of dicts
		# and pass it to the pandas constructor.
		# Django has a handy method to transform a queryset into a list of dicts,
		# but we can't really use it because we need to retrieve foreign keys, and it
		# can only retrieve either bare attributes or the ones we specify, so we'd
		# need to either hardcode everything or run it twice and merge it. Easier
		# to write our own, unfortunately. It's quite a bit slower than the Django though
		# so maybe we can speed it up somehow. Maybe doing it as a raw SQL query and then
		# dropping any excess fields would be better. Going to leave that for another
		# day right now.

		foreign_keys = ["region", "crop", "rainfall_set"]

		record_model = globals()[self.record_model_name]
		fields = [f.name for f in record_model._meta.get_fields()]  # get all the fields for calibrated parameters
		basic_fields = list(set(fields) - set(foreign_keys))  # remove the foreign keys - we'll process those separately

		# reverse_name will exist for subclasses
		data = getattr(self, self.reverse_name).all()  # get all the records for this set
		output = []
		for record in data:
			# if we were told to skip this region, don't add it - could also do this in pandas after conversion
			if exclude_regions and record.region.internal_id in exclude_regions:
				continue

			output_dict = {}
			for field in basic_fields:  # apply the basic fields directly into a dictionary and coerce to floats
				field_value = getattr(record, field)
				output_dict[field] = float(field_value) if type(field_value) is decimal.Decimal else field_value
			output_dict["i"] = record.crop.crop_code  # but then grab the specific attributes of the foreign keys we wawnt
			output_dict["g"] = record.region.internal_id
			output.append(output_dict)  # put the dict into the list so we can make a DF of it

		return pandas.DataFrame(output)  # construct a data frame and send it back

	def to_csv(self, *args, **kwargs):
		"""
			Saves the set to a CSV file - all args are passed through to Pandas.to_csv, so it's
			possible to have it return a CSV as a string by just calling to_csv()
		:param args: waterspout_sort_columns is not compatible with waterspout_limited
		:param kwargs:
		:return:
		"""
		df = self.as_data_frame().sort_values(axis=0, by=["year", "g", "i"])
		df = df.rename(columns={"g": "region", "i": "crop"})

		if kwargs.pop("waterspout_sort_columns", False) is True:
			# match the column output to how Spencer has it so we can compare
			column_order = ("region", "crop", "year", "omegaland", "omegasupply", "omegalabor",
			                "omegaestablish", "omegacash", "omeganoncash", "omegatotal",
			                "xwater", "p", "y", "xland", "omegawater", "sigma", "theta",
			                "pimarginal", "rho", "betaland", "betawater", "betasupply",
			                "betalabor", "tau", "gamma", "delta", "xlandsc", "xwatersc",
			                "xdiffland", "xdifftotalland", "xdiffwater", "resource_flag")
			df = df.reindex(columns=column_order)

		if kwargs.pop("waterspout_limited", False) is True:
			columns = settings.LIMITED_RESULTS_FIELDS
			df = df[columns]

		if "index" not in kwargs:  # if the caller doesn't specify an option for pandas' index, set it to False explicitly so it doesn't export the index
			kwargs["index"] = False

		return df.to_csv(*args, **kwargs)


class InputDataSet(RecordSet):
	model_area = models.ForeignKey(ModelArea, on_delete=models.CASCADE, related_name="input_data")
	reverse_name = "input_data_set"


class CalibrationSet(RecordSet):
	model_area = models.ForeignKey(ModelArea, on_delete=models.CASCADE, related_name="calibration_data")
	record_model_name = "CalibratedParameter"
	reverse_name = "calibration_set"


class RainfallSet(RecordSet):
	model_area = models.ForeignKey(ModelArea, on_delete=models.CASCADE, related_name="rainfall_data")
	reverse_name = "rainfall_set"
	record_model_name = "RainfallParameter"


class ResultSet(RecordSet):
	reverse_name = "result_set"
	record_model_name = "Result"

	model_run = models.ForeignKey("ModelRun", null=True, blank=True,
	                               on_delete=models.CASCADE, related_name="results")

	date_run = models.DateTimeField(default=django.utils.timezone.now, null=True, blank=True)

	# store the dapper version that the model ran with - that way we can detect if an updated version might provide different results
	dapper_version = models.CharField(max_length=20)

	# in_calibration indicates whether or not the results have any negative profits
	# or have otherwise fallen outside of calibrated values.
	in_calibration = models.BooleanField(default=True)
	# not using in_calibration_text for now. We'll have the web app figure out
	# which records are negative profits and show a table if in_calibration is false
	#in_calibration_text = models.TextField(null=True, blank=True)

	infeasibilities_text = models.TextField(null=True, blank=True)
	# infeasibilities reverse relation

	def __str__(self):
		return f"Results for Model Run {self.model_run.name} from Dapper {self.dapper_version} at {self.date_run}"


class ModelItem(models.Model):
	"""

		Fields that are allowed to be null are ones that aren't part of calibration, but instead may be set for final
		results
	"""
	class Meta:
		abstract = True
		indexes = [
			models.Index(fields=("year",))
		]

	crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
	region = models.ForeignKey(Region, on_delete=models.CASCADE)
	year = models.IntegerField(null=True, blank=True)  # inputs will have this, but calibrated items and results may not
	omegaland = models.DecimalField(max_digits=10, decimal_places=1)
	omegasupply = models.DecimalField(max_digits=10, decimal_places=1)
	omegalabor = models.DecimalField(max_digits=10, decimal_places=1)
	omegaestablish = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True)
	omegacash = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True)
	omeganoncash = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True)
	omegatotal = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True)
	p = models.DecimalField(max_digits=18, decimal_places=10)
	y = models.DecimalField(max_digits=13, decimal_places=5)
	xland = models.DecimalField(max_digits=18, decimal_places=10)


class InputDataItem(ModelItem):
	class Meta:
		unique_together = ['crop', 'region', 'year']

	dataset = models.ForeignKey(InputDataSet, on_delete=models.CASCADE, related_name="input_data_set")

	xwater = models.DecimalField(max_digits=18, decimal_places=10)

	serializer_fields = ["crop", "region", "year", "omegaland",
	                     "omegasupply", "omegalabor", "omegaestablish", "omegacash",
	                     "omeganoncash", "omegatotal", "p", "y", "xland", "xwater"]


class CalibratedParameter(ModelItem):
	"""
		Note that it's of class ModelItem - ModelItems define the various input
		parameters and results that we use for calibration inputs, calibrated
		parameters, and model results
	"""

	class Meta:
		unique_together = ['crop', 'region', 'year']

	xwater = models.DecimalField(max_digits=18, decimal_places=10)
	omegawater = models.DecimalField(max_digits=10, decimal_places=2)
	pc = models.DecimalField(max_digits=10, decimal_places=3)
	sigma = models.DecimalField(max_digits=5, decimal_places=4)
	theta = models.DecimalField(max_digits=5, decimal_places=4)
	pimarginal = models.DecimalField(max_digits=18, decimal_places=10)
	#alphaland = models.DecimalField(max_digits=11, decimal_places=10, null=True, blank=True)
	# alphawater = models.DecimalField(max_digits=11, decimal_places=10, null=True, blank=True)
	# alphasupply = models.DecimalField(max_digits=11, decimal_places=10, null=True, blank=True)
	# alphalabor = models.DecimalField(max_digits=11, decimal_places=10, null=True, blank=True)
	rho = models.DecimalField(max_digits=15, decimal_places=10)
	# lambdaland = models.DecimalField(max_digits=15, decimal_places=10, null=True, blank=True)
	#lambdacrop = models.DecimalField(max_digits=15, decimal_places=10, null=True, blank=True)
	betaland = models.DecimalField(max_digits=18, decimal_places=10)
	betawater = models.DecimalField(max_digits=18, decimal_places=10)
	betasupply = models.DecimalField(max_digits=18, decimal_places=10)
	betalabor = models.DecimalField(max_digits=18, decimal_places=10)
	tau = models.DecimalField(max_digits=18, decimal_places=10)
	gamma = models.DecimalField(max_digits=18, decimal_places=10)
	delta = models.DecimalField(max_digits=18, decimal_places=10)
	#xlandcalib = models.DecimalField(max_digits=18, decimal_places=10, null=True, blank=True)
	#xwatercalib = models.DecimalField(max_digits=18, decimal_places=10, null=True, blank=True)
	#difflandpct = models.DecimalField(max_digits=12, decimal_places=10, null=True, blank=True)
	#diffwaterpct = models.DecimalField(max_digits=12, decimal_places=10, null=True, blank=True)

	# this item helps us check on the front end whether or not modifications will send profits negative.
	# we'll store it here since it comes out of the calibration and will be per region/crop combination
	price_yield_correction_factor = models.DecimalField(max_digits=6, decimal_places=3, default=1)

	calibration_set = models.ForeignKey(CalibrationSet, on_delete=models.CASCADE, related_name="calibration_set")
	serializer_fields = ["crop", "region", "price_yield_correction_factor"]

						#["crop", "region", "year", "omegaland", "omegawater",
	                    # "omegasupply", "omegalabor", "omegaestablish", "omegacash",
	                    # "omeganoncash", "omegatotal", "p", "y", "price_yeild_correction_factor"]


class RainfallParameter(ModelItem):
	class Meta:
		unique_together = ['crop', 'region', 'year']

	rainfall_set = models.ForeignKey(RainfallSet, on_delete=models.CASCADE, related_name="rainfall_set")

	coef_intercept = models.DecimalField(max_digits=10, decimal_places=5)
	twin = models.DecimalField(max_digits=10, decimal_places=5)
	tspr = models.DecimalField(max_digits=10, decimal_places=5)
	tsum = models.DecimalField(max_digits=10, decimal_places=5)
	coef_tsum = models.DecimalField(max_digits=10, decimal_places=5)
	coef_tspr = models.DecimalField(max_digits=10, decimal_places=5)
	coef_twin = models.DecimalField(max_digits=10, decimal_places=5)
	ptspr = models.DecimalField(max_digits=10, decimal_places=5)
	ptwin = models.DecimalField(max_digits=10, decimal_places=5)
	ptsum = models.DecimalField(max_digits=10, decimal_places=5)
	coef_ptspr = models.DecimalField(max_digits=10, decimal_places=5)
	coef_ptwin = models.DecimalField(max_digits=10, decimal_places=5)
	coef_ptsum = models.DecimalField(max_digits=10, decimal_places=5)
	coef_crop = models.DecimalField(max_digits=10, decimal_places=5)


class Result(ModelItem):
	"""
		Holds the results for a single region/crop
	"""

	omegawater = models.DecimalField(max_digits=10, decimal_places=2)
	resource_flag = models.CharField(max_length=5, null=True, blank=True)
	# we may be able to drop these fields later, but they help us while we're comparing to the original DAP and our validation
	xlandsc = models.DecimalField(max_digits=18, decimal_places=10, null=True, blank=True)
	xwatersc = models.DecimalField(max_digits=18, decimal_places=10, null=True, blank=True)
	xdiffland = models.DecimalField(max_digits=18, decimal_places=10, null=True, blank=True)
	xdifftotalland = models.DecimalField(max_digits=18, decimal_places=10, null=True, blank=True)
	xdiffwater = models.DecimalField(max_digits=18, decimal_places=10, null=True, blank=True)

	result_set = models.ForeignKey(ResultSet, on_delete=models.CASCADE, related_name="result_set")

	net_revenue = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True)
	gross_revenue = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True)
	water_per_acre = models.DecimalField(max_digits=18, decimal_places=5, null=True, blank=True)


class RainfallResult(models.Model):
	serializer_fields = ["region", "crop", "calc_yield", "gross_revenue"]

	result_set = models.ForeignKey(ResultSet, on_delete=models.CASCADE, related_name="rainfall_result_set")

	region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="rainfall_results")
	crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name="rainfall_results")

	# yield is the only real result from the rainfall statistical model, so that's what we're storing, but we'll also
	# want to store some of the same main results as the Result items so we can merge them
	calc_yield = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True)
	gross_revenue = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True)

	# these aren't yet really outputs, but we need to include them for the viz to work correctly
	xlandsc = models.DecimalField(max_digits=18, decimal_places=10, null=True, blank=True)
	xwatersc = models.DecimalField(max_digits=18, decimal_places=10, null=True, blank=True)


class ModelRun(models.Model):
	"""
		The central object for configuring an individual run of the model - is related to modification objects from the
		modification side.
	"""
	class Meta:
		indexes = [
			models.Index(fields=("ready", "running", "complete")),
			models.Index(fields=("date_submitted",))
		]
	name = models.CharField(max_length=255)
	description = models.TextField(null=True, blank=True)

	ready = models.BooleanField(default=False, null=False)  # marked after the web interface adds all modifications
	running = models.BooleanField(default=False, null=False)  # marked while in processing
	complete = models.BooleanField(default=False, null=False)  # tracks if the model has actually been run for this result yet

	status_message = models.CharField(max_length=2048, default="", null=True, blank=True)  # for status info or error messages
	result_values = models.TextField(default="", null=True, blank=True)
	log_data = models.TextField(null=True, blank=True)  # we'll store log outputs from the model run here.
	date_submitted = models.DateTimeField(default=django.utils.timezone.now, null=True, blank=True)
	date_completed = models.DateTimeField(null=True, blank=True)

	# which model run is the base, unmodified version? Useful for data viz
	base_model_run = models.ForeignKey("ModelRun", null=True, blank=True, on_delete=models.DO_NOTHING)
	is_base = models.BooleanField(default=False)  # is this a base model run (True), or a normal model run (False)

	# model_area relation is through calibration_set
	calibration_set = models.ForeignKey(CalibrationSet, on_delete=models.CASCADE, related_name="model_runs")
	calibrated_parameters_text = models.TextField(null=True, blank=True)  # we'll put a snapshot of the calibration parameters in here, probably
												# as a CSV. This way, if people eidt the calibration data for future runs,
												# we still know what inputs ran this version of the model.

	rainfall_set = models.ForeignKey(RainfallSet, on_delete=models.CASCADE, related_name="model_runs", null=True, blank=True)

	user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="model_runs")
	organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="model_runs")

	# region_modifications - back-reference from related content
	# crop_modifications - back-reference from related content

	serializer_fields = ['id', 'name', 'description', 'ready', 'running', 'complete', 'status_message',
		                'date_submitted', 'date_completed', "calibration_set", "rainfall_set",
						 "user_id", "organization", "base_model_run_id", "is_base",
	                     "land_modifications_average", "water_modifications_average",
	                     "price_modifications_average", "yield_modifications_average"]

	def __str__(self):
		return f"Model Run: {self.name}"

	def as_dict(self):
		return {field: getattr(self, field) for field in self.serializer_fields}

	def as_json(self):
		# using the Django serializer class handles datetimes, etc properly
		return json.dumps(self.as_dict(), cls=django.core.serializers.json.DjangoJSONEncoder)

	def _get_modification_average(self, queryset_name, property_name):
		mods = list(getattr(self, queryset_name).all())
		num_items = len(mods)
		if num_items == 0:
			return 0
		return float(sum([getattr(mod, property_name) for mod in mods]))/num_items

	@property
	def land_modifications_average(self):
		return self._get_modification_average("region_modifications", "land_proportion")

	@property
	def water_modifications_average(self):
		return self._get_modification_average("region_modifications", "water_proportion")

	@property
	def price_modifications_average(self):
		return self._get_modification_average("crop_modifications", "price_proportion")

	@property
	def yield_modifications_average(self):
		return self._get_modification_average("crop_modifications", "yield_proportion")

	@property
	def scenario_df(self):
		df = self.get_df(self.calibration_set)
		# save the calibration data with any modifications as a text string to the DB - will exclude scenario
		# level constraints though!
		self.calibrated_parameters_text = df.to_csv()  # if we don't provide a path to to_csv, it returns a string
		self.save()
		return df

	@property
	def rainfall_df(self):
		if self.rainfall_set:
			return self.get_df(self.rainfall_set)
		else:
			return None

	def get_df(self, base_model):
		"""
			Given the currently attached modifications, etc, returns a complete calibration DF
		:return:
		"""

		# we'll not send static or removed regions through the model, so drop them here
		# for removed regions, this is all we need to do - for static regions, we'll
		# pull their base case results later when we process results
		excludes = self.region_modifications.filter(Q(removed=True) | Q(hold_static=True))
		if excludes:
			exclude_ids = [mod.region.internal_id for mod in excludes]
		else:
			exclude_ids = None

		# pull initial calibration dataset as it is
		df = base_model.as_data_frame(exclude_regions=exclude_ids)

		# do any overrides or changes from the modifications

		return df

	def attach_modifications(self, scenario):
		land_modifications = {}
		water_modifications = {}
		rainfall_modifications = {}

		region_modifications = self.region_modifications.filter(region__isnull=False)
		for modification in region_modifications:  # get all the nondefault modifications
			land_modifications[modification.region.internal_id] = float(modification.land_proportion)
			if modification.region.supports_irrigation:
				water_modifications[modification.region.internal_id] = float(modification.water_proportion)
			if modification.region.supports_rainfall:
				rainfall_modifications[modification.region.internal_id] = float(modification.rainfall_proportion)

		default_region_modification = self.region_modifications.get(region__isnull=True)

		scenario.perform_adjustment("land", land_modifications, default=float(default_region_modification.land_proportion))

		# attach modifications for irrigation and rainfall depending on what the model area supports
		if self.calibration_set.model_area.supports_irrigation:
			scenario.perform_adjustment("water", water_modifications, default=float(default_region_modification.water_proportion))
		if self.calibration_set.model_area.supports_rainfall:
			scenario.perform_adjustment("rainfall", rainfall_modifications, default=float(default_region_modification.rainfall_proportion))

		region_linked_key = "region_linked"
		# now attach the crop modifications - start by loading the data into a dict
		price_modifications = {region_linked_key: []}
		yield_modifications = {region_linked_key: []}
		crop_modifications = self.crop_modifications.filter(crop__isnull=False)
		for modification in crop_modifications:  # get all the nondefault modifications

			crop_code = modification.crop.crop_code

			if modification.region is None:  # if it's not region-linked
				price_modifications[crop_code] = float(modification.price_proportion)
				yield_modifications[crop_code] = float(modification.yield_proportion)
				region_id = None
			else:   # if it is region-linked
				region_id = modification.region.internal_id

				# create dictionaries for both price and yield constraints that include
				# the region ID, the crop code, and the value
				price_modifications["region_linked"].append({
					"region": region_id,
					"crop": crop_code,
					"value": float(modification.price_proportion),
				})
				yield_modifications["region_linked"].append({
					"region": region_id,
					"crop": crop_code,
					"value": float(modification.yield_proportion),
				})

			max_crop_area_constraint = modification.max_land_area_proportion
			if max_crop_area_constraint and modification.min_land_area_proportion and not max_crop_area_constraint > modification.min_land_area_proportion:
				# if the max and the min are both defined and the max is less than the min, skip adding the max -
				# this is because stormchaser uses a value of -1 as its max value to indicate no upper limit
				max_crop_area_constraint = None

			# we can always add it, and it's OK if they're both None - that'll get checked later
			scenario.add_crop_area_constraint(crop_code=modification.crop.crop_code,
			                                  min_proportion=modification.min_land_area_proportion,
			                                  max_proportion=max_crop_area_constraint,
			                                  region=region_id)

		default_crop_modification = self.crop_modifications.get(crop__isnull=True)
		# then pass those dicts to the scenario code regardless if there are items (so defaults get set)
		scenario.perform_adjustment("price", price_modifications, default=float(default_crop_modification.price_proportion))
		scenario.perform_adjustment("yield", yield_modifications, default=float(default_crop_modification.yield_proportion))

	def run(self, csv_output=None):
		# initially, we won't support calibrating the data here - we'll
		# just use an initial calibration set and then make our modifications
		# before running the scenarios

		#calib = calibration.ModelCalibration(run.calbration_df)
		#calib.calibrate()

		self.running = True
		self.save()  # mark it as running and save it so the API updates the status
		try:
			scenario_runner = scenarios.Scenario(calibration_df=self.scenario_df, rainfall_df=self.rainfall_df)
			self.attach_modifications(scenario=scenario_runner)
			results = scenario_runner.run()

			if csv_output is not None:
				results.to_csv(csv_output)

			# before loading results, make sure we weren't deleted in the app between starting the run and now
			try:
				ModelRun.objects.get(pk=self.id)
			except ModelRun.DoesNotExist:
				return

			# now we need to load the resulting df back into the DB
			result_set = self.load_records(results_df=results, rainfall_df=scenario_runner.rainfall_df)
			self.load_infeasibilities(scenario_runner, result_set)

			self.complete = True
			log.info("Model run complete")
		finally:  # make sure to mark it as not running regardless of its status or if it crashes
			self.running = False
			self.save()

	def load_records(self, results_df, rainfall_df=None):
		"""
			Given a set of model results, loads the results to the database
		:param results_df:
		:param model_run:
		:return:
		"""
		log.info(f"Loading results for model run {self.id}")
		result_set = ResultSet(model_run=self, dapper_version=get_dapper_version())
		result_set.save()

		# load the PMP results first
		self._load_df(results_df=results_df, result_set=result_set, record_model=Result)
		# now load the rainfall data if it applies
		if rainfall_df is not None:
			self._load_df(results_df=rainfall_df, result_set=result_set, record_model=RainfallResult)

	def _load_df(self, results_df, result_set, record_model=Result):
		try:
			for record in results_df.itertuples():
				# get the first tuple's fields, then exit the loop
				# this should be faster than retrieving it every time in the next loop, but we need to do it once
				fields = list(set(record._fields) - set(["id", "g", "i", "calibration_set"]))
				break

			for record in results_df.itertuples():  # returns named tuples
				result = record_model(result_set=result_set)
				result.crop = Crop.objects.get(crop_code=record.i, model_area=self.calibration_set.model_area)
				result.region = Region.objects.get(internal_id=record.g, model_area=self.calibration_set.model_area)
				for column in fields:  # _fields isn't private - it's just preventing conflicts - see namedtuple docs
					value = getattr(record, column)

					if value is not None and type(value) is not str and numpy.isnan(value):  # if we got NaN (such as with an infeasibility) - filter out None values because they make numpy.isnan fail
						value = None  # then we need to skip it or it'll bork the whole table (seriously)

					setattr(result, column, value)

				if not result.net_revenue or result.net_revenue < 0:  # if any record has negative net revenues, we're out of bounds on calibration - mark it
					result_set.in_calibration = False

				result.save()

			if result_set.in_calibration is False:  # if we changed the in_calibration value, save the result set - we check this here so we only trigger the save once
				result_set.save()

			return result_set
		except:
			result_set.delete()  # clean up if we fail while loading data
			raise

	def load_infeasibilities(self, scenario, result_set):
		log.debug("Assessing infeasibilities")
		for infeasibility in scenario.infeasibilities:
			Infeasibility.objects.create(result_set=result_set,
			                             region=Region.objects.get(internal_id=infeasibility.region, model_area=self.calibration_set.model_area),
			                             year=infeasibility.timeframe,
			                             description=infeasibility.description
			                             )

		total_infeasibilities = len(scenario.infeasibilities)
		crops = {}
		# now let's see if there are any crops that are common to the infeasibilities
		#if total_infeasibilities > 2:  # if we have more than a handful, we'll assess which crops are common
		for infeasibility in scenario.infeasibilities:
			infeasible_region_results = Result.objects.filter(result_set=result_set,
					                                          region__internal_id=infeasibility.region,
					                                          year=infeasibility.timeframe)

			for result in infeasible_region_results:
				crop = result.crop.crop_code
				if crop in crops:
					crops[crop] += 1
				else:
					crops[crop] = 1

		# ideally we'd want to key this by name so that we can show the name here
		if len(crops.keys()) > 0:
			sorted_by_appearance = {k:v for k,v in sorted(crops.items(), key=lambda item: item[1], reverse=True)}
			infeasibility_items = ["{} ({})".format(crop, value) for crop, value in sorted_by_appearance.items()]
			self.infeasibilities_text = ", ".join(infeasibility_items)


class Infeasibility(models.Model):
	result_set = models.ForeignKey(ResultSet, on_delete=models.CASCADE, related_name="infeasibilities")
	year = models.SmallIntegerField()
	region = models.ForeignKey(Region, null=True, on_delete=models.SET_NULL, related_name="infeasibilities")
	description = models.TextField()


class RegionModification(models.Model):
	"""
		A modification on a region to use in a model run. We'll need to have the model run build a new pandas data frame
		from these based on the code inputs and the model adjustments
	"""
	class Meta:
		unique_together = ['model_run', 'region']

	# we have two nullable foreign keys here. If both are new, then the rule applies to the whole model area as the default.
	# if only one is active, then it applies to either the region, or the group (and then we need something that applies
	# it to the individual regions). It's possible that the group->individual application will occur in the JS because
	# we'll want to display it all in a map, but we might want to do it here so that API calls can use the groups too
	region = models.ForeignKey(Region,
	                           on_delete=models.CASCADE,
	                           related_name="modifications",
	                           null=True, blank=True)
	region_group = models.ForeignKey(RegionGroup,
	                                 on_delete=models.CASCADE,
	                                 related_name="modifications",
	                                 null=True, blank=True)

	water_proportion = models.FloatField(default=1.0, blank=True)  # the amount, relative to base values, to provide
	rainfall_proportion = models.FloatField(default=1.0, blank=True)  # the amount, relative to base values, to provide
	land_proportion = models.FloatField(default=1.0, blank=True)

	# extra flags on regions
	hold_static = models.BooleanField(default=False)  # should this region be held static during modeling? If so, it's not passed to the model at all and results are pulled from the base case
	removed = models.BooleanField(default=False)  # should this region be removed from the model entirely? If so, it's filtered from the dataset passed into the model and nothing additional is added

	model_run = models.ForeignKey(ModelRun, blank=True, on_delete=models.CASCADE, related_name="region_modifications")

	serializer_fields = ["id", "region", "region_group", "water_proportion", "land_proportion", "rainfall_proportion",
	                     "hold_static", "removed"]


class CropModification(models.Model):
	"""
		A modification on a crop to use in a model run. We'll need to have the model run build a new pandas data frame
		from these based on the code inputs and the model adjustments
	"""
	class Meta:
		unique_together = ['model_run', 'crop']

	serializer_fields = ["id", "crop", "crop_group", "price_proportion", "yield_proportion",
	                     "min_land_area_proportion", "max_land_area_proportion"]

	crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name="modifications",
	                            null=True, blank=True)
	region = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name="crop_modifications",
	                            null=True, blank=True)  # we'll be allowing region-tied crop modifications in a future update - as of 2021/March/02, there is no logic for handling this value yet - it'll all be null and won't go into the solver anywhere
	crop_group = models.ForeignKey(CropGroup, on_delete=models.CASCADE, related_name="modifications",
	                               null=True, blank=True)

	price_proportion = models.FloatField(default=1.0, blank=True)  # the amount, relative to base values, to provide
	yield_proportion = models.FloatField(default=1.0, blank=True)  # the amount, relative to base values, to provide
	min_land_area_proportion = models.FloatField(null=True, blank=True)  # the amount, relative to base values, to provide
	max_land_area_proportion = models.FloatField(null=True, blank=True)  # the amount, relative to base values, to provide

	model_run = models.ForeignKey(ModelRun, null=True, blank=True, on_delete=models.CASCADE, related_name="crop_modifications")


class HelpDocument(models.Model):
	"""
		We'll store help documents in the DB as well so that they can
		be pulled into the app via the API - we can also publish them
		elswhere if we'd like - this is ultimately just a simple article
		system.

		We'll plan to load these from specific articles in the Sphinx
		documentation
	"""
	title = models.CharField(max_length=2048)
	author = models.ForeignKey(User, on_delete=models.DO_NOTHING)
	slug = models.CharField(max_length=64)

	summary = models.TextField()
	body = models.TextField()



