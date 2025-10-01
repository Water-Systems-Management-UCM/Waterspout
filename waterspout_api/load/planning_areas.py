from . import general
from . import core

def load_planning_areas():
	params_file = core.get_data_file_path("planning_area", "params.json")
	general.load_generic(params_file)