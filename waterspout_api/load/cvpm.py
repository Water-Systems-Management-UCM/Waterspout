from . import general
from . import core

def load_cvpm():
	params_file = core.get_data_file_path("cvpm", "params.json")
	general.load_generic(params_file)