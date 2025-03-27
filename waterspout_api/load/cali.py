from . import general
from . import core

def load_cali():
	params_file = core.get_data_file_path("cali", "params.json")
	general.load_generic(params_file)