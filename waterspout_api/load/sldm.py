from . import general
from . import core

def load_sldm():
	params_file = core.get_data_file_path("sldm", "params.json")
	general.load_generic(params_file)