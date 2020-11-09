import json
import os
import csv
import logging

from waterspout_api import models

from Waterspout.settings import BASE_DIR

log = logging.getLogger("waterspout.load")


def reset_model_area(model_area_name, organization):
	# this could return more than one object, but if it does, we want the error to
	# make sure we aren't clearing a bunch of things we don't want to clear
	try:
		model_area = models.ModelArea.objects.get(name=model_area_name, organization=organization)
		model_area.delete()
	except models.ModelArea.DoesNotExist:
		pass

	model_area = models.ModelArea(name=model_area_name, organization=organization)
	model_area.save()

	# do any other cleanup here - regions will cascade delete

	return model_area


def reset_organization(org_name):
	# this could return more than one object, but if it does, we want the error to
	# make sure we aren't clearing a bunch of things we don't want to clear
	try:
		org = models.Organization.objects.get(name=org_name)
		org.delete()
	except models.Organization.DoesNotExist:
		pass

	org_group = models.Group(name=org_name)
	org_group.save()
	organization = models.Organization(name=org_name, group=org_group)
	organization.save()
	# do any other cleanup here - regions will cascade delete

	return organization


def get_data_file_path(project, filename):
	"""
		Gets the path of data files we've stored for each project
	:param project:
	:return:
	"""
	return os.path.join(BASE_DIR, "waterspout_api", "data", project, filename)


def load_regions(json_file, field_map, model_area):
	"""
		Given a geojson file, loads each record as a region instance, assigning data
		to fields by the field map. Fields in the field map that aren't available on
		the model will be loaded as "extra" attributes, available by filtering
		`region.extras.filter(name == "{attribute_name}")`, for example.

		Warning: It loads the *whole* geojson record in as geometry, even attributes that
		aren't in the field map, so all attributes will be sent to the client. If you don't
		want this or want a leaner GeoJSON, strip unnecessary information out before loading
	:param json_file: newline delimited GeoJSON file (QGIS can export this) of the regions
	:param field_map: iterable of two-tuples. First value is the field in the datasets,
					and the second is the field here in waterspout (think "from", "to")
	:param model_area: The model area instance to attach these regions to
	:return:
	"""

	with open(json_file, 'r') as input_data:
		geojson = input_data.readlines()

	for record in geojson:
		# make a Python version of the JSON record
		python_data = json.loads(record)
		region = models.Region()  # make a new region object
		region.geometry = record  # save the whole JSON record as the geometry we'll send to the browser in the future
		region.model_area = model_area
		region.save()  # save it immediately because we'll need to set foreign keys to it on key failures below

		for fm in field_map:  # apply all the attributes to the region based on the field map
			value = python_data["properties"][fm[0]]
			if hasattr(region, fm[1]):  # we need to check if that attribute exists first
				setattr(region, fm[1], value)  # if it does, set it on the region object
			else:  # if it doesn't have that attribute, then we'll create an Extra and relate it
				extra = models.RegionExtra(region=region, name=fm[1], value=value)
				extra.save()

		region.save()  # save it with the new attributes


def load_calibration_set(csv_file, model_area, years):
	calibration_set = models.CalibrationSet(model_area=model_area, years=",".join([str(year) for year in years]))
	calibration_set.save()

	with open(csv_file, 'r') as csv_data:
		reader = csv.DictReader(csv_data)
		for row in reader:
			param = models.CalibratedParameter(calibration_set=calibration_set)
			for key in row:
				# need to do lookups for foreign keys
				if key == "g":
					param.region = models.Region.objects.get(internal_id=row["g"], model_area=model_area)
				elif key == "i":
					param.crop = models.Crop.objects.get(crop_code=row["i"], model_area=model_area)
				else:
					setattr(param, key, row[key])

			param.save()

	return calibration_set


def get_or_create_system_user():
	return models.User.objects.get_or_create(username="system")[0]


def add_system_user_to_org(org):
	system_user = get_or_create_system_user()
	system_user.groups.add(org.group)  # add the system user to this group
	system_user.save()