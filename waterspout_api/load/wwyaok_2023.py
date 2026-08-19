from . import general
from . import core

def load_wwyaok_2023():
	params_file = core.get_data_file_path("WWYAOA2023", "params.json")
	general.load_generic(params_file)