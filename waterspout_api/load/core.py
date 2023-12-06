import json
import os
import csv
import logging

import pandas
import django

from waterspout_api import models, load

from Waterspout.settings import BASE_DIR

log = logging.getLogger("waterspout.load")


def reset_model_area(model_area_name, data_folder, organization, latitude, longitude, default_zoom, feature_package, help_page_content=None):
	# this could return more than one object, but if it does, we want the error to
	# make sure we aren't clearing a bunch of things we don't want to clear

	try:
		model_area = models.ModelArea.objects.get(name=model_area_name, organization=organization)
	except models.ModelArea.DoesNotExist:
		model_area = models.ModelArea(name=model_area_name, data_folder=data_folder, organization=organization,
		                              map_center_latitude=latitude, map_center_longitude=longitude,
		                              map_default_zoom=default_zoom, feature_package_name=feature_package,
		                              main_help_page_content=help_page_content)
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
			value = python_data["properties"][fm[0]]  # fm[0] is the file's field name and fm[1] is the name in our model.
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
						param.year = row["year"]
				else:
					setattr(param, key, row[key])

			if not continue_outer:
				param.save()

	return item_set


def detect_rainfall_and_irrigation(model_area, rainfall_year=None):
	"""
		After we load irrigation and rainfall input datasets, we need to detect which regions have data for each item.
		For each record, xland contains the amount of area, and we only support each of these items if
		1) It has a record and
		2) That record is more than 5% of the combined irrigated/rainfall ag for at least one crop in the area
	:param model_area:
	:return:
	"""

	regions = model_area.region_set.all()
	for region in regions:
		# set some defaults so we don't have to worry about complex logic - we can set it to true as many times as we like later
		region.supports_rainfall = False
		region.supports_irrigation = False

		for crop in model_area.crop_set.all():
			try:
				kwargs = {}
				if rainfall_year:
					kwargs["year"] = rainfall_year
				rainfall_record = models.RainfallParameter.objects.get(crop=crop, region=region, **kwargs)
			except models.RainfallParameter.DoesNotExist:
				rainfall_record = None

			try:
				irrigation_record = models.CalibratedParameter.objects.get(crop=crop, region=region)
			except models.CalibratedParameter.DoesNotExist:
				irrigation_record = None

			# handle the case for the crop isn't in the region
			if rainfall_record is None and irrigation_record is None:
				continue
			# handle the case where it's only irrigated in this region
			elif rainfall_record is None:
				region.supports_irrigation = True
				continue
			# handle the case where it's only rainfall in this region
			elif irrigation_record is None:
				region.supports_rainfal = True
				continue

			# Now handle it having records for both - we'll only use both
			# if they're each more than 5% of the total land area (per Alvar)
			total_land = rainfall_record.xland + irrigation_record.xland
			if rainfall_record.xland / total_land > 0.05:
				region.supports_rainfall = True
			else:  # if it's less than 5%, merge the rainfall land area for the crop into the irrigated area
				irrigation_record.xland += rainfall_record.xland
				irrigation_record.save()

			if irrigation_record.xland / total_land > 0.05:
				region.supports_irrigation = True
			else:  # if it's less than 5%, merge the irrigated area into the rainfall-ag area for the region.
				rainfall_record.xland += irrigation_record.xland
				rainfall_record.save()

		region.save()


def get_or_create_system_user():
	return models.User.objects.get_or_create(username="system")[0]


def add_system_user_to_org(org):
	system_user = get_or_create_system_user()
	system_user.groups.add(org.group)  # add the system user to this group
	system_user.save()


def create_base_case(organization, calibration_set, rainfall_set):
	mr = models.ModelRun(name="Base Case",
	                               organization=organization,
	                               user=get_or_create_system_user(),
	                               is_base=True,
	                               calibration_set=calibration_set,
	                               rainfall_set=rainfall_set,
	                               ready=True
	                               )
	mr.save()

	models.RegionModification.objects.create(model_run=mr)
	models.CropModification.objects.create(model_run=mr)


def load_crops(crop_file, model_area):
	"""
		This is a temporary hack, mostly, because this isn't a crop file - we should replace
		this later
	:param calibration_file:
	:param organization:
	:return:
	"""
	with open(crop_file, 'r') as crop_data:
		crop_csv = csv.DictReader(crop_data)
		for row in crop_csv:
			try:
				models.Crop(crop_code=row["code"], name=row["name"], model_area=model_area).save()
			except django.db.utils.IntegrityError:
				pass  # if it already exists, skip it


def load_multipliers(multipliers_file,
					 model_area,
					 RegionModel=models.Region,
					 CropModel=models.Crop,
					 MultipliersModel=models.EmploymentMultipliers,
					 ):
	"""
		Creates or updates the multipliers for the regions in the given model area
	:param multipliers_file: should have a key "internal_id" for the region ID that matches the region's internal ID (WRIA, DAP, etc)
	:param model_area:
	:return:
	"""

	with open(multipliers_file, 'r') as multipliers_data:
		multipliers_csv = csv.DictReader(multipliers_data)
		for row in multipliers_csv:
			# get the existing RegionMultipliers object that the row corresponds to. If it doesn't exist, create it
			if "crop_code" in row:
				crop_code = row["crop_code"]
			else:
				crop_code = None
			try:
				mults = MultipliersModel.objects.get(region__internal_id=row["internal_id"], crop__crop_code=crop_code, region__model_area=model_area)
			except MultipliersModel.DoesNotExist:
				region = RegionModel.objects.get(internal_id=row["internal_id"], model_area=model_area)
				if crop_code:
					crop = CropModel.objects.get(crop_code=crop_code, model_area=model_area)
				else:
					crop = None
				mults = MultipliersModel.objects.create(region=region, crop=crop)

			# apply the multipliers from the spreadsheet
			for mult in ("total_revenue", "direct_value_add", "total_value_add", "direct_jobs", "total_jobs"):
				setattr(mults, mult, row[mult])

			mults.save()


def load_dap_style_inputs(area_name, data_name, regions, calibration_file, data_file, crop_file,
				years, latitude, longitude, default_zoom, region_field_map, feature_package, rainfall_file=None,
                          multipliers_file=None, organization=None, help_page_content_file=None,
						  **kwargs):
	"""

	:param area_name:
	:param data_name:
	:param regions:
	:param calibration_file:
	:param data_file:
	:param crop_file:
	:param years:
	:param latitude:
	:param longitude:
	:param default_zoom:
	:param region_field_map:
	:param feature_package:
	:param rainfall_file:
	:param multipliers_file:
	:param organization: If an organization is provided, it will be used for the model area
	:return:
	"""

	if organization is None:
		log.info("Creating organization")
		organization = reset_organization(org_name=area_name)

		add_system_user_to_org(org=organization)

	if help_page_content_file is not None:
		with open(get_data_file_path(data_name, help_page_content_file), 'r') as help_file:
			help_page_content = " ".join(help_file.readlines())
	else:
		help_page_content = None

	log.info("Creating model area")
	model_area = reset_model_area(model_area_name=f"Load: {area_name}", data_folder=data_name, organization=organization,
	                                   latitude=latitude, longitude=longitude, default_zoom=default_zoom, feature_package=feature_package,
	                                    help_page_content=help_page_content)


	log.info("Loading Regions")
	load_regions(json_file=get_data_file_path(data_name, regions),
	             field_map=region_field_map,
	             model_area=model_area)

	log.info("Loading Crops")
	load_crops(get_data_file_path(data_name, crop_file), model_area)


	if calibration_file:
		log.info("Loading Calibration Set")
		calibration_set = load_input_data_set(csv_file=get_data_file_path(data_name, calibration_file),
	                          model_area=model_area,
	                          years=years)
	else:
		if kwargs["features"]["has_calibration_data"]:
			raise ValueError("No calibration file specified, but input says it has calibration data")
		else:  # if no file and has_calibration_data is False
			# we just make an empty calibration set, but it has no data -
			# this holds assumptions about the data model together for the most part
			calibration_set = models.CalibrationSet.objects.create(model_area=model_area)

	if rainfall_file is not None:
		log.info("Loading Rainfall Data")
		rainfall_set = load_input_data_set(csv_file=get_data_file_path(data_name, rainfall_file),
	                                    model_area=model_area,
	                                    years=years,
	                                    item_model=models.RainfallParameter,
	                                    set_model=models.RainfallSet,
	                                    set_lookup="rainfall_set")
	else:
		rainfall_set = None

	if multipliers_file is not None:
		log.info("Loading Multipliers")
		load_multipliers(multipliers_file=get_data_file_path(data_name, multipliers_file),
		                               model_area=model_area)

	if data_file:
		log.info("Loading Input Data")
		input_data_set = load_input_data_set(csv_file=get_data_file_path(data_name, data_file),
									model_area=model_area,
									years=years,
									item_model=models.InputDataItem,
									set_model=models.InputDataSet,
	                                set_lookup="dataset")
	else:
		if kwargs["features"]["has_input_data"]:
			raise ValueError("No input data file specified, but input says it has an input data file")

	if not "detect_rainfall_irrigation_split" in kwargs or kwargs["detect_rainfall_irrigation_split"] is True:
		log.info("Detecting Rainfall and Irrigation Split")
		detect_rainfall_and_irrigation(model_area)

	if "create_base_case" not in kwargs or kwargs["create_base_case"] is True:
		log.info("Creating Base Case")
		create_base_case(calibration_set=calibration_set,
	                 rainfall_set=rainfall_set,
	                  organization=organization)

	return model_area


def reset_organization_for_reload(model_area, area_name):
	"""
		Basically removes the model area and recreates it, but keeps the same organization. This is a full cleanout, meant
		for situations where we're actually replacing regions, crops, etc - replacing inputs aside from just the calibration
		data.
	:param model_area: the ModelArea object to reset - we'll keep the organization attached to it intact
	:param area_name - which module loads the organization again?
	:return:
	"""

	# get the organization off the model area
	organization = model_area.organization

	# delete the model area - if we set everything up correctly, the deletion will correctly cascade
	model_area.delete()

	# trigger the specified loader
	area_module = getattr(load, area_name)
	loader_name = f"load_{area_name}"
	loader = getattr(area_module, loader_name)
	loader(organization=organization)



def load_region_group_file(group_file_path, member_file_path, config_path, model_area,
						   RegionGroupSetModel=models.RegionGroupSet,
						   RegionGroupModel=models.RegionGroup,
						   RegionModel=models.Region):
	"""
		Includes definition of models to use because it's used in a migration and we'll need to pass
		in the migration's version of the model
	"""

	with open(config_path, 'r') as config_data:
		config = json.load(config_data)

	# we already have a unique constraint on these, but if we check here it'd be good so we don't end up
	# applying a failed migration
	if RegionGroupSetModel.objects.filter(name=config["group_set_name"], model_area=model_area).exists():
		log.warning(f"Group Set {config['group_set_name']} already exists. Will not create again.")
		return False

	# then make the group set and the objects
	group_set = RegionGroupSetModel(name=config["group_set_name"], model_area=model_area)
	group_set.save()

	# some checks below fail to detect the first group set is an instance of RegionGroupSet when this is run as a migration
	# so we'll get it straight from the DB now that it's created, based on the PK. We won't modify it now, so I think
	# this should be safe
	#group_set = models.RegionGroupSet.objects.get(pk=group_set.id)

	# now create the groups in the geojson file
	with open(group_file_path, 'r') as group_info_file:
		for line in group_info_file.readlines():
			RegionGroupModel.objects.create(
				name=json.loads(line)["properties"][config["group_name_field"]],
				group_set=group_set,
				geometry=line
			)

	# then add the null group for all other regions
	if "null_group_name" in config:
		RegionGroupModel.objects.create(name=config["null_group_name"], group_set=group_set)

	with open(member_file_path, 'r') as group_members_file:
		groups = list(csv.DictReader(group_members_file))  # read it all in - we're going to go through it twice

	# get the distinct list of group names - this was how we originally figured out which groups to make. Now do it with
	# the GeoJSON file so we can add geometries
	#group_names = list(set([region_group[config["group_name"]] for region_group in groups]))
	#group_names.append(config["null_group_name"])

	for region_group in group_set.groups.all():
		# now add the regions to the group - seems most efficient to iterate through the group data while we already have
		# this object in hand - we'll go through the data multiple times, but we'll do far fewer DB retrievals for group objects
		for region_group_info in groups:
			if region_group_info[config["group_name_field"]] == region_group.name or (
				region_group.name == config["null_group_name"] and (region_group_info[config["group_name_field"]] is None or region_group_info[config["group_name_field"]] == "")):

				region_filter = {'model_area': model_area}
				# we have variable names for the fields involved, so we'll need to use dictionary expansion for this
				region_filter[config["region_key"]] = region_group_info[config["region_match_key"]]
				try:
					region = RegionModel.objects.get(**region_filter)
				except RegionModel.DoesNotExist:
					log.info(f"Failed to retrieve region with ID {config['region_key']}={region_group_info[config['region_match_key']]} with region data {region_group_info}")
					raise

				region_group.regions.add(region)

	# function should check that group set name doesn't already exist in model area and gracefully exit if it does

def preload_model_runs(model_runs, data_name, model_area):
	for preload_run in model_runs:  # keys are CSV files in the base_folder, values are params
		if preload_run.startswith("_"):  # skip the comments
			continue

		preload_run_data = model_runs[preload_run]
		user = models.User.objects.get(username=preload_run_data["user"])
		if "model_run_kwargs" in preload_run_data:
			kwargs = preload_run_data["model_run_kwargs"]
		else:
			kwargs = {}

		kwargs["complete"] = False
		kwargs["user"] = user

		preload_file = get_data_file_path(data_name, preload_run)
		load_single_model_run(preload_file, model_runs[preload_run], model_area, model_run_kwargs=kwargs)


def load_single_model_run(filepath, params, model_area, model_run_kwargs):
	calibration_set = model_area.calibration_data.first()

	results = pandas.read_csv(filepath)
	model_run = models.ModelRun.objects.create(name=params['name'],
											   calibration_set=calibration_set,
											   organization=calibration_set.model_area.organization,
											   **model_run_kwargs
											   )
	model_run.load_records(results_df=results)
	model_run.complete = True
	model_run.save()
