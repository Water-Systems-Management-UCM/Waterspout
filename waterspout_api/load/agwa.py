# Washington Loading Code

from . import core


def load_agwa(organization=None):
	area_name = "WA"
	data_name = "washington"

	zoom = 7
	lon = -120.476
	lat = 47.419

	core.load_dap_style_inputs(area_name=area_name,
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