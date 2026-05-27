from . import general
from . import core

def load_calsim3():
	params_file = core.get_data_file_path("calsim3", "params.json")
	general.load_generic(params_file)