import logging
import traceback

import django
from django.db import models  # we're going to geodjango this one - might not need it, but could make some things nicer
from django.contrib.auth.models import User, Group

import pandas
import arrow

log = logging.getLogger("waterspout.models")

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


class ModelArea(models.Model):
	"""
		This would be something like "The Delta", or "Washington" - mostly, this will be one to one with organizations,
		but just in case we want to be able to deploy multiple models for an organization in the future, we'll store it
		this way.
	"""
	organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.DO_NOTHING)
	name = models.CharField(max_length=255, unique=True)
	description = models.TextField(null=True, blank=True)

	def __str__(self):
		return self.name
	

class RegionGroup(models.Model):
	name = models.CharField(max_length=255, null=False, blank=False)
	internal_id = models.CharField(max_length=100, null=False, blank=False)  # typically we have some kind of known ID to feed to a model that means something to people
	model_area = models.ForeignKey(ModelArea, on_delete=models.CASCADE)

	geometry = models.TextField(null=True, blank=True)  # this will just store GeoJSON and then we'll combine into collections manually


class Region(models.Model):
	name = models.CharField(max_length=255, null=False, blank=False)
	internal_id = models.CharField(max_length=100, null=False, blank=False, unique=True)  # typically we have some kind of known ID to feed to a model that means something to people
	external_id = models.CharField(max_length=100, null=True, blank=True)  # a common external identifier of some kind
	# .extra_attributes reverse lookup

	geometry = models.TextField(null=True, blank=True)  # this will just store GeoJSON and then we'll combine into collections manually

	model_area = models.ForeignKey(ModelArea, on_delete=models.CASCADE)
	group = models.ForeignKey(RegionGroup, null=True, blank=True, on_delete=models.CASCADE)  # there could be a reason to make it a many to many instead, but
																	# I can't think of a use case right now, and it'd require some PITA
																	# logic to tease apart specifications for regions in overlapping groups

	def __str__(self):
		return "Area {}: Region {}".format(self.model_area.name, self.name)


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
		unique_together = ['crop_code', 'organization']

	name = models.CharField(max_length=255, null=False, blank=False)  # human readable crop name
	crop_code = models.CharField(max_length=30, null=False, blank=False)  # code used in the models (like ALFAL for Alfalfa)
	organization = models.ForeignKey(Organization, on_delete=models.CASCADE)  # clear any crops for an org when deleted


class CropGroup(models.Model):
	"""
		A unit to group individual crops together - note that we need to crop groups are also by organization and
		the same crop group exist for multiple organizations
	"""
	name = models.CharField(max_length=255, null=False, blank=False)
	crops = models.ManyToManyField(Crop)  # Each crop can be in many groups


class CalibrationSet(models.Model):
	"""
		For storing the results of calibration parameters that come out of phase 1 of the model - we'll load a few sets
		of calibrated parameters initially, but then provide a black box version of the calibration parameters. We can
		then have behavior that tries a lookup for a calibration set, and if it doesn't exist, runs the calibration.
	"""
	years = models.TextField()  # yes, text. We'll concatenate text as a year lookup
	# prices = model

	model_area = models.ForeignKey(ModelArea, on_delete=models.CASCADE)
	# calibrated_parameters - backward relationship from CalibratedParameter

	def as_data_frame(self):
		"""
			Returns the data frame that needs to be run through the model itself
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

		foreign_keys = ["g", "i"]
		fields = [f.name for f in CalibratedParameter._meta.get_fields()]  # get all the fields for calibrated paramters
		basic_fields = list(set(fields) - set(foreign_keys))  # remove the foreign keys - we'll process those separately

		data = self.calibrated_parameters.all()  # get all the records for this set
		output = []
		for record in data:
			output_dict = {}
			for field in basic_fields:  # apply the basic fields directly into a dictionary
				output_dict[field] = getattr(record, field)
			output_dict["i"] = record.i.crop_code  # but then grab the specific attributes of the foreign keys we wawnt
			output_dict["g"] = record.g.internal_id
			output.append(output_dict)  # put the dict into the list so we can make a DF of it

		return pandas.DataFrame(output)  # construct a data frame and send it back


class ModelItem(models.Model):
	class Meta:
		abstract = True

	i = models.ForeignKey(Crop, on_delete=models.DO_NOTHING)
	g = models.ForeignKey(Region, on_delete=models.DO_NOTHING)
	year = models.CharField(max_length=10)  # one might think this should be an integer, but they sometimes do this thing of assigning a year like 2015.5. It's still categorical in this case though, so making it a char field to not have precision issues
	omegaland = models.DecimalField(max_digits=10, decimal_places=1)
	omegasupply = models.DecimalField(max_digits=10, decimal_places=1)
	omegalabor = models.DecimalField(max_digits=10, decimal_places=1)
	omegaestablish = models.DecimalField(max_digits=10, decimal_places=1)
	omegacash = models.DecimalField(max_digits=10, decimal_places=1)
	omeganoncash = models.DecimalField(max_digits=10, decimal_places=1)
	omegatotal = models.DecimalField(max_digits=10, decimal_places=1)
	xwater = models.DecimalField(max_digits=18, decimal_places=10)
	p = models.DecimalField(max_digits=18, decimal_places=10)
	y = models.DecimalField(max_digits=13, decimal_places=5)
	xland = models.DecimalField(max_digits=18, decimal_places=10)
	omegawater = models.DecimalField(max_digits=10, decimal_places=2)
	sigma = models.DecimalField(max_digits=5, decimal_places=4)
	theta = models.DecimalField(max_digits=5, decimal_places=4)
	pimarginal = models.DecimalField(max_digits=18, decimal_places=10)
	alphaland = models.DecimalField(max_digits=11, decimal_places=10)
	alphawater = models.DecimalField(max_digits=11, decimal_places=10)
	alphasupply = models.DecimalField(max_digits=11, decimal_places=10)
	alphalabor = models.DecimalField(max_digits=11, decimal_places=10)
	rho = models.DecimalField(max_digits=15, decimal_places=10)
	lambdaland = models.DecimalField(max_digits=15, decimal_places=10)
	lambdacrop = models.DecimalField(max_digits=15, decimal_places=10)
	betaland = models.DecimalField(max_digits=18, decimal_places=10)
	betawater = models.DecimalField(max_digits=18, decimal_places=10)
	betasupply = models.DecimalField(max_digits=18, decimal_places=10)
	betalabor = models.DecimalField(max_digits=18, decimal_places=10)
	tau = models.DecimalField(max_digits=18, decimal_places=10)
	gamma = models.DecimalField(max_digits=18, decimal_places=10)
	delta = models.DecimalField(max_digits=18, decimal_places=10)
	xlandcalib = models.DecimalField(max_digits=18, decimal_places=10)
	xwatercalib = models.DecimalField(max_digits=18, decimal_places=10)
	difflandpct = models.DecimalField(max_digits=12, decimal_places=10)
	diffwaterpct = models.DecimalField(max_digits=12, decimal_places=10)


class CalibratedParameter(ModelItem):
	"""
		Note that it's of class ModelItem - ModelItems define the various input
		parameters and results that we use for calibration inputs, calibrated
		parameters, and model results
	"""
	calibration_set = models.ForeignKey(CalibrationSet, on_delete=models.CASCADE, related_name="calibrated_parameters")


class ModelRun(models.Model):
	"""
		The central object for configuring an individual run of the model - is related to modification objects from the
		modification side.
	"""
	ready = models.BooleanField(default=False, null=False)  # marked after the web interface adds all modifications
	running = models.BooleanField(default=False, null=False)  # marked while in processing
	complete = models.BooleanField(default=False, null=False)  # tracks if the model has actually been run for this result yet
	status_message = models.CharField(max_length=2048, default="", null=True, blank=True)  # for status info or error messages
	result_values = models.TextField(default="", null=True, blank=True)
	log_data = models.TextField(null=True, blank=True)  # we'll store log outputs from the model run here.
	date_submitted = models.DateTimeField(default=django.utils.timezone.now, null=True, blank=True)
	date_completed = models.DateTimeField(null=True, blank=True)

	calibration_set = models.ForeignKey(CalibrationSet, on_delete=models.DO_NOTHING)
	calibrated_parameters_text = models.TextField()  # we'll put a snapshot of the calibration parameters in here, probably
												# as a CSV. This way, if people eidt the calibration data for future runs,
												# we still know what inputs ran this version of the model.

	user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="model_runs")
	organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="model_runs")

	# region_modifications - back-reference from related content
	# crop_modifications - back-reference from related content

	def load_result(self, values):
		pass

	@property
	def scenario_df(self):
		"""
			Given the currently attached modifications, etc, returns a complete calibration DF
		:return:
		"""

		# pull initial calibration dataset as it is

		# do any overrides or changes from the modifications

		#

		# TODO: Need to do much more than this, but for now, just return the existing calib set
		return self.calibrated_parameters_text


class Result(ModelItem):
	"""
		Holds the results for a single region/crop
	"""
	model_run = models.ForeignKey(ModelRun, on_delete=models.CASCADE)



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
	                           on_delete=models.DO_NOTHING,
	                           related_name="modifications",
	                           null=True, blank=True)
	region_group = models.ForeignKey(RegionGroup,
	                                 on_delete=models.DO_NOTHING,
	                                 related_name="modifications",
	                                 null=True, blank=True)

	water_proportion = models.FloatField()  # the amount, relative to base values, to provide
	land_proportion = models.FloatField()

	model_run = models.ForeignKey(ModelRun, null=True, blank=True, on_delete=models.CASCADE, related_name="region_modifications")


class CropModification(models.Model):
	"""
		A modification on a crop to use in a model run. We'll need to have the model run build a new pandas data frame
		from these based on the code inputs and the model adjustments
	"""
	class Meta:
		unique_together = ['model_run', 'crop']

	crop = models.ForeignKey(Crop, on_delete=models.DO_NOTHING, related_name="modifications")
	crop_group = models.ForeignKey(CropGroup, on_delete=models.DO_NOTHING, related_name="modifications")

	price_proportion = models.FloatField()  # the amount, relative to base values, to provide
	yield_proportion = models.FloatField()  # the amount, relative to base values, to provide
	min_land_area_proportion = models.FloatField()  # the amount, relative to base values, to provide
	max_land_area_proportion = models.FloatField()  # the amount, relative to base values, to provide

	model_run = models.ForeignKey(ModelRun, null=True, blank=True, on_delete=models.CASCADE, related_name="crop_modifications")


