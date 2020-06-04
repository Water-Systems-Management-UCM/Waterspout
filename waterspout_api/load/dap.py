# DAP Loading Code


from . import core

data_name = "dap"  # used to find files relative to the data folder
area_name = "DAP"


def load_dap(regions="delta_islands_wDAP.geojson"):
	core.reset_model_area(model_area_name=area_name)
	core.load_regions(json_file=core.get_data_file_path(data_name, regions),
	                  field_map=(
		                  ("NAME", "name"),
		                  ("DAP_Region_ID", "internal_id"),
		                  ("DLIS_ID", "external_id"),
		                  ("DeltaZone", "DeltaZone"),
		                  ("Suisun", "Suisun")
	                  ),
	                  area_name=area_name)