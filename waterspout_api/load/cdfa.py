from . import general
from . import core

def load_cdfa():
	params_file = core.get_data_file_path("cdfa", "params.json")
	general.load_generic(params_file)