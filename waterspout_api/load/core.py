import json
import os
import csv
import logging

import django

from waterspout_api import models

from Waterspout.settings import BASE_DIR

log = logging.getLogger("waterspout.load")


def reset_model_area(model_area_name, data_folder, organization, latitude, longitude, default_zoom, feature_package):
	# this could return more than one object, but if it does, we want the error to
	# make sure we aren't clearing a bunch of things we don't want to clear

	try:
		model_area = models.ModelArea.objects.get(name=model_area_name, organization=organization)
	except models.ModelArea.DoesNotExist:
		model_area = models.ModelArea(name=model_area_name, data_folder=data_folder, organization=organization,
		                              map_center_latitude=latitude, map_center_longitude=longitude,
		                              map_default_zoom=default_zoom, feature_package_name=feature_package)
		model_area.save()

	# do any other cleanup here - regions will cascade delete

	return model_area


def reset_organization(org_name):
	# this could return more than one object, but if it does, we want the error to
	# make sure we aren't clearing a bunch of things we don't want to clear
	try:
		org_group = models.Group.objects.get(name=org_name)
	except models.Group.DoesNotExist:
		org_group = models.Group(name=org_name)
		org_group.save()

	try:
		organization = models.Organization.objects.get(name=org_name)
	except models.Organization.DoesNotExist:
		organization = models.Organization(name=org_name, group=org_group)
		organization.save()

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


def load_input_data_set(csv_file, model_area, years,
                         set_model=models.CalibrationSet,
                         item_model=models.CalibratedParameter,
                         set_lookup="calibration_set"):
	"""
		Load Input Data or Calibration Data, but they use the same format - just the calibration data will store
		more fields. provide the set_model, item_model, and set_lookup in order to use it for input data
	:param csv_file:
	:param model_area:
	:param years:
	:param set_model: which model to use for the dataset
	:param item_model: which model to use for individual data items
	:param set_lookup: string for the foreign key from the item_model to the set_model
	:return:
	"""
	item_set = set_model(model_area=model_area, years=",".join([str(year) for year in years]))
	item_set.save()

	with open(csv_file, 'r') as csv_data:
		reader = csv.DictReader(csv_data)
		for row in reader:
			continue_outer = False  # we need a flag in case we don't find an existing region object so we can skip it from the internal loop

			param = item_model()
			setattr(param, set_lookup, item_set)  # set the foreign key to the item_set - equiv to calibration_set=item_set if for calibration data
			for key in row:
				# need to do lookups for foreign keys
				if key == "g":
					try:
						param.region = models.Region.objects.get(internal_id=row["g"], model_area=model_area)
					except models.Region.DoesNotExist:
						continue_outer = True
						break
				elif key == "i":
					param.crop = models.Crop.objects.get(crop_code=row["i"], model_area=model_area)
				elif key == "year":
					if "." in row["year"]:
						param.year = 1  # set year = 1 for calibration data sets
				else:
					setattr(param, key, row[key])

			if not continue_outer:
				param.save()

	return item_set


def get_or_create_system_user():
	return models.User.objects.get_or_create(username="system")[0]


def add_system_user_to_org(org):
	system_user = get_or_create_system_user()
	system_user.groups.add(org.group)  # add the system user to this group
	system_user.save()


def create_base_case(organization, calibration_set):
	mr = models.ModelRun(name="Base Case",
	                               organization=organization,
	                               user=get_or_create_system_user(),
	                               is_base=True,
	                               calibration_set=calibration_set,
	                               ready=True
	                               )
	mr.save()

	models.RegionModification.objects.create(model_run=mr)
	models.CropModification.objects.create(model_run=mr)


def load_crops(calibration_file, model_area):
	"""
		This is a temporary hack, mostly, because this isn't a crop file - we should replace
		this later
	:param calibration_file:
	:param organization:
	:return:
	"""
	with open(calibration_file, 'r') as calib_data:
		calib_csv = csv.DictReader(calib_data)
		for row in calib_csv:
			try:
				models.Crop(crop_code=row["code"], name=row["name"], model_area=model_area).save()
			except django.db.utils.IntegrityError:
				pass  # if it already exists, skip it


def load_dap_style_inputs(area_name, data_name, regions, calibration_file, data_file, crop_file,
				years, latitude, longitude, default_zoom, region_field_map, feature_package):

	organization = reset_organization(org_name=area_name)

	add_system_user_to_org(org=organization)

	model_area = reset_model_area(model_area_name=f"Load: {area_name}", data_folder=data_name, organization=organization,
	                                   latitude=latitude, longitude=longitude, default_zoom=default_zoom, feature_package=feature_package)

	load_regions(json_file=get_data_file_path(data_name, regions),
	             field_map=region_field_map,
	             model_area=model_area)
	load_crops(get_data_file_path(data_name, crop_file), model_area)
	calibration_set = load_input_data_set(csv_file=get_data_file_path(data_name, calibration_file),
	                          model_area=model_area,
	                          years=years)

	input_data_set = load_input_data_set(csv_file=get_data_file_path(data_name, data_file),
									model_area=model_area,
									years=years,
									item_model=models.InputDataItem,
									set_model=models.InputDataSet,
	                                set_lookup="dataset")

	create_base_case(calibration_set=calibration_set,
	                  organization=organization)