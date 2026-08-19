from . import general
from . import core

def load_wwyaok_2021():
	params_file = core.get_data_file_path("WWYAOA2021", "params.json")
	general.load_generic(params_file)