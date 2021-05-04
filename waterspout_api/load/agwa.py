# Washington Loading Code

from . import core


def load_agwa():
	area_name = "WA"
	data_name = "washington"

	zoom = 7
	lon = -120.476
	lat = 47.419

	core.load_dap_style_inputs(area_name=area_name,
								data_name=data_name,
								regions="WRIA/new_WRIA_300m_alt.geojsonl.json",
								calibration_file="WA_DAP_format_calibrated.csv",
								data_file="OpenAgWA_consolidated_Annual_02152021.csv",
								crop_file="crop_codes.csv",
								years=list(range(2008, 2019)),
								latitude=lat,
								longitude=lon,
								default_zoom=zoom,
								region_field_map=(
									("WRIA_NM", "name"),
									("WRIA_NR_New", "internal_id"),
								),
	                            feature_package="WSDA",
	                            rainfall_file="dryland_database.csv",
	                            multipliers_file="newwria_with_regions_and_multipliers.csv"
	                           )