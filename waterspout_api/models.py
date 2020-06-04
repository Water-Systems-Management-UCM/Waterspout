import logging
import traceback

import django
from django.db import models  # we're going to geodjango this one - might not need it, but could make some things nicer
from django.contrib.auth.models import User, Group

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

	group = models.OneToOneField(Group, on_delete=models.DO_NOTHING)


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
	internal_id = models.CharField(max_length=100, null=False, blank=False)  # typically we have some kind of known ID to feed to a model that means something to people
	external_id = models.CharField(max_length=100, null=False, blank=False)  # a common external identifier of some kind
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


class CalibratedParameter(models.Model):
	calibration_set = models.ForeignKey(CalibrationSet, on_delete=models.CASCADE)


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
	calibrated_parameters = models.TextField()  # we'll put a snapshot of the calibration parameters in here, probably
												# as a CSV. This way, if people eidt the calibration data for future runs,
												# we still know what inputs ran this version of the model.
	user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="model_runs")
	organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="model_runs")

	# modifications - backward relationship

	def get_area_to_run(self):
		"""
			Returns a two-tuple of items to area id, subarea_id to pass to the mantis server
		"""
		area = None
		possible_areas = ("county", "b118_basin", "cvhm_farm", "subbasin")
		for area_value in possible_areas:
			possible_area = getattr(self, area_value)
			if possible_area is not None:
				area = possible_area
				break
		else:
			return 1, 0  # 1 is central valley, 0 is because there's no subitem

		area_type_id = mantis_area_map_id[type(area).__name__]  # we key the ids based on the class being used - this is clunky, but efficient

		return area_type_id, area.mantis_id

	def load_result(self, values):
		self.result_values = ",".join([str(item) for item in values])
		self.date_run = arrow.utcnow().datetime

	def run(self):
		"""
			Runs Mantis and sets the status codes. Saves automatically at the end
		:return:
		"""
		try:
			# TODO: Fix below
			results = None
			self.load_result(values=results)
			self.complete = True
			self.status_message = "Successfully run"
		except:
			log.error("Failed to run Model. Error was: {}".format(traceback.format_exc()))
			self.complete = True
			self.status_message = "Model run failed. This error has been reported."

		self.save()


class RegionModification(models.Model):
	"""
		A modification on a region to use in a model run. We'll need to have the model run build a new pandas data frame
		from these based on the code inputs and the model adjustments
	"""
	class Meta:
		unique_together = ['model_run', 'region']

	region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, related_name="modifications")
	water_proportion = models.FloatField()  # the amount, relative to base values, to provide

	model_run = models.ForeignKey(ModelRun, null=True, blank=True, on_delete=models.CASCADE, related_name="modifications")