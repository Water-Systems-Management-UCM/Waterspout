# DAP Loading Code


from . import core

data_name = "dap"  # used to find files relative to the data folder

def load_dap(regions="delta_islands.geojson"):
	core.load_regions(json_file=core.get_data_file_path(data_name, regions),
	                  field_map=(
		                  ("NAME", "name"),
		                  ("DLIS_ID", "external_id"),
		                  ("DeltaZone", "DeltaZone"),
		                  ("Suisun", "Suisun")
	                  ),
	                  area_name="DAP")