from . import general
from . import core

def load_walla_yakima():
	params_file = core.get_data_file_path("walla_yakima", "params.json")
	general.load_generic(params_file)