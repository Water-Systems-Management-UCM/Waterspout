# DAP Loading Code
import csv

import django

from waterspout_api import models
from . import core

data_name = "dap"  # used to find files relative to the data folder
area_name = "DAP"


def load_dap(regions="delta_islands_wDAP.geojson",
             calibration_file="DAP_calibrated.csv"):
	organization = core.reset_organization(org_name=area_name)
	model_area = core.reset_model_area(model_area_name=area_name, organization=organization)
	load_regions(regions, model_area)
	load_crops(core.get_data_file_path(data_name, calibration_file), organization)
	load_calibration(calibration_file, model_area, organization=organization)


def load_regions(regions, model_area):
	core.load_regions(json_file=core.get_data_file_path(data_name, regions),
	                  field_map=(
		                  ("NAME", "name"),
		                  ("DAP_Region_ID", "internal_id"),
		                  ("DLIS_ID", "external_id"),
		                  ("DeltaZone", "DeltaZone"),
		                  ("Suisun", "Suisun")
	                  ),
	                  model_area=model_area)


def load_calibration(calibration_file, model_area, organization):
	core.load_calibration_set(csv_file=core.get_data_file_path(data_name, calibration_file),
	                          model_area=model_area,
	                          years=[2014,2015,2016,2017],
	                          organization=organization
	                          )


def load_crops(calibration_file, organization):
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
				models.Crop(crop_code=row["i"], organization=organization).save()
			except django.db.utils.IntegrityError:
				pass  # if it already exists, skip it