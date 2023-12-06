from . import general
from . import core

def load_ca_cv():
	params_file = core.get_data_file_path("ca_cv", "params.json")
	general.load_generic(params_file)