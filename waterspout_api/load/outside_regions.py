from . import general
from . import core

def load_outside_regions():
	params_file = core.get_data_file_path("outside_regions", "params.json")
	general.load_generic(params_file)