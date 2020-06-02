from django.db import models  # we're going to geodjango this one - might not need it, but could make some things nicer



class Organization(models.Model):
	"""
		Since this application is designed to support multiple models, possibly in the same instance, make most things
		be ties to an "organization" of some kind - we'll include users in the organization and arrange permissions
		around users within the organization.
	"""
	name = models.CharField(max_length=255, null=False, blank=False)


class RegionGroup(models.Model):
	name = models.CharField(max_length=255, null=False, blank=False)
	internal_id = models.CharField(max_length=100, null=False, blank=False)  # typically we have some kind of known ID to feed to a model that means something to people
	organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

	geometry = models.TextField(null=True, blank=True)  # this will just store GeoJSON and then we'll combine into collections manually


class Region(models.Model):
	name = models.CharField(max_length=255, null=False, blank=False)
	internal_id = models.CharField(max_length=100, null=False, blank=False)  # typically we have some kind of known ID to feed to a model that means something to people

	geometry = models.TextField(null=True, blank=True)  # this will just store GeoJSON and then we'll combine into collections manually

	organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
	group = models.ForeignKey(RegionGroup, on_delete=models.CASCADE)  # there could be a reason to make it a many to many instead, but
																	# I can't think of a use case right now, and it'd require some PITA
																	# logic to tease apart specifications for regions in overlapping groups



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


class CalibratedParameter(models.Model):
	"""
		For storing the results of calibration paramters that come out of phase 1 of the model - we don't store the
		calibration routines here - if you have questions about the routines that generate these parameters, get in
		touch with Josué Medellin-Azuara.
	"""
	pass
