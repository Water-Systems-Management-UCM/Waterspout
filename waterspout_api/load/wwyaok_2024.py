from . import general
from . import core

def load_wwyaok_2024():
	params_file = core.get_data_file_path("WWYAOA2024", "params.json")
	general.load_generic(params_file)