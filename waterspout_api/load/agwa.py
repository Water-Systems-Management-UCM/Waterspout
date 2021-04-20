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
								regions="WRIA/wrias.geojson",
								calibration_file="WA_DAP_format_calibrated.csv",
								data_file="WA_consolidated_inputs_DAP_format.csv",
								crop_file="crop_codes.csv",
								years=list(range(2008, 2019)),
								latitude=lat,
								longitude=lon,
								default_zoom=zoom,
								region_field_map=(
									("WRIA_NM", "name"),
									("WRIA_ID", "internal_id"),
								),
	                            feature_package="WSDA"
	                           )