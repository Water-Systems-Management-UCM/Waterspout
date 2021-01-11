# DAP Loading Code
import csv

import django

from waterspout_api import models
from . import core

data_name = "dap"  # used to find files relative to the data folder
area_name = "DAP"


def load_dap(regions="delta_islands_wDAP_simplified_0005.geojson",
             calibration_file="DAP_calibrated.csv",
             data_file="DAP_input.csv",
             crop_file="crop_codes.csv",
             years=(2014, 2015, 2016, 2017),):
	core.load_dap_style_inputs(area_name=area_name,
								data_name=data_name,
								regions="delta_islands_wDAP_simplified_0005.geojson",
								calibration_file="DAP_calibrated.csv",
								data_file="DAP_input.csv",
								crop_file="crop_codes.csv",
								years=(2014, 2015, 2016, 2017),
	                            latitude=38.10,
	                            longitude=-121.50,
	                            default_zoom=9,
	                            region_field_map=(
									("NAME", "name"),
									("DAP_Region_ID", "internal_id"),
									("DLIS_ID", "external_id"),
									("DeltaZone", "DeltaZone"),
									("Suisun", "Suisun")
								)
	                           )

def old_load_dap(
			regions="delta_islands_wDAP_simplified_0005.geojson",
             calibration_file="DAP_calibrated.csv",
             data_file="DAP_input.csv",
             crop_file="crop_codes.csv",
             years=(2014, 2015, 2016, 2017),
             ):

	organization = core.reset_organization(org_name=area_name)

	core.add_system_user_to_org(org=organization)

	model_area = core.reset_model_area(model_area_name=f"Load: {area_name}", organization=organization,
	                                   latitude=38.10, longitude=-121.50, default_zoom=9)

	load_regions(regions, model_area)
	core.load_crops(core.get_data_file_path(data_name, crop_file), model_area)
	calibration_set = load_calibration(calibration_file, model_area, years)
	input_data_set = load_input_data(data_file, model_area, years)

	load_initial_runs(calibration_set=calibration_set,
	                  organization=organization)


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


def load_calibration(calibration_file, model_area, years):
	return core.load_input_data_set(csv_file=core.get_data_file_path(data_name, calibration_file),
	                          model_area=model_area,
	                          years=years
	                          )


def load_input_data(data_file, model_area, years):
	return core.load_input_data_set(csv_file=core.get_data_file_path(data_name, data_file),
									model_area=model_area,
									years=years,
									item_model=models.InputDataItem,
									set_model=models.InputDataSet,
	                                set_lookup="dataset"
	                          )



def load_initial_runs(calibration_set, organization):
	core.create_base_case(organization=organization, calibration_set=calibration_set)