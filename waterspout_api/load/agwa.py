# Washington Loading Code

from . import core
from waterspout_api import models
import os

area_name = "WA"
data_name = "washington"

def load_agwa(organization=None):


	zoom = 7
	lon = -120.476
	lat = 47.419

	model_area = core.load_dap_style_inputs(area_name=area_name,
								data_name=data_name,
								regions="WRIA/new_WRIA_300m_alt_wbehavior.geojsonl.json",
								calibration_file="WA_DAP_format_calibrated.csv",
								data_file="WA_full_inputs_for_data_viewer_annual.csv",
								crop_file="crop_codes.csv",
								years=list(range(2008, 2019)),
								latitude=lat,
								longitude=lon,
								default_zoom=zoom,
								region_field_map=(
									("WRIA_NM", "name"),
									("WRIA_NR_New", "internal_id"),
									("default_behavior", "default_behavior"),
								),
	                            feature_package="WSDA",
	                            rainfall_file="dryland_database3.csv",
	                            multipliers_file="newwria_with_regions_and_multipliers.csv",
	                            organization=organization,
	                            help_page_content_file="help_content.html"
	                           )
	load_groups(model_area)


def load_groups(model_area,
							group_definition_file=core.get_data_file_path(data_name, os.path.join("region_groups", "groups.geojsonl")),
							group_membership_file=core.get_data_file_path(data_name, os.path.join("region_groups", "groups.csv")),
							group_config_file=core.get_data_file_path(data_name, os.path.join("region_groups", "groups.json")),
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
	RegionModel.objects.filter(external_id=None, name="Proratable Yakima").update(internal_id=-4)
	RegionModel.objects.filter(external_id=None, name="Non-proratable Yakima Basin").update(internal_id=-2)
	RegionModel.objects.filter(external_id=None, name="Western WA").update(internal_id=-1)
	RegionModel.objects.filter(external_id=None, name="Eastern WA").update(internal_id=-3)
