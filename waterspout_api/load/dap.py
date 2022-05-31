# DAP Loading Code
import os

from waterspout_api import models
from . import core

data_name = "dap"  # used to find files relative to the data folder
area_name = "DAP"


def load_dap(regions="delta_islands_wDAP_simplified_0005.geojson",
             calibration_file="DAP_calibrated.csv",
             data_file="DAP_input.csv",
             crop_file="crop_codes.csv",
             years=(2014, 2015, 2016, 2017),
             organization=None):
	model_area = core.load_dap_style_inputs(area_name=area_name,
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
								),
	                            feature_package="DAP_DSC",
	                            organization=organization,
	                            help_page_content_file="help_content.html"
	                           )

	load_water_agency_groups(model_area)
	load_multipliers(model_area)


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


def load_water_agency_groups(model_area,
							group_definition_file=core.get_data_file_path(data_name, os.path.join("region_groups", "Water Agencies.geojsonl")),
							group_membership_file=core.get_data_file_path(data_name, os.path.join("region_groups", "Water Agencies.csv")),
							group_config_file=core.get_data_file_path(data_name, os.path.join("region_groups", "Water Agencies.json")),
							RegionGroupSetModel=models.RegionGroupSet,
							RegionGroupModel=models.RegionGroup,
							RegionModel=models.Region):

	# first, add negative external_ids for the delta aggregate areas so we can match them with group membership
	correct_dlis_ids(RegionModel)

	core.load_region_group_file(group_file_path=group_definition_file,
								member_file_path=group_membership_file,
								config_path=group_config_file,
								model_area=model_area,
								RegionGroupSetModel=RegionGroupSetModel,
								RegionGroupModel=RegionGroupModel,
								RegionModel=RegionModel
							)


def correct_dlis_ids(RegionModel=models.Region):
	# do it with a filter/update because we might have multiple regions that meet this criteria
	# also only do it if the external ID is already null so we don't mess with anything else
	RegionModel.objects.filter(external_id=None, name="NORTH DELTA AGGREGATE AREA").update(external_id=-1)
	RegionModel.objects.filter(external_id=None, name="CENTRAL DELTA AGGREGATE AREA").update(external_id=-2)
	RegionModel.objects.filter(external_id=None, name="SOUTH DELTA AGGREGATE AREA").update(external_id=-3)


def load_multipliers(model_area,
		data_file=core.get_data_file_path(data_name, "DAP_multipliers_processed.csv"),
		RegionModel=models.Region,
		CropModel=models.Crop,
		MultipliersModel=models.EmploymentMultipliers
		):

	core.load_multipliers(data_file, model_area, RegionModel=RegionModel, CropModel=CropModel,
						  MultipliersModel=MultipliersModel)