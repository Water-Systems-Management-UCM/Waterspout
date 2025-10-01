from . import general
from . import core

def load_cdfa2():
	params_file = core.get_data_file_path("cdfa2", "params.json")
	general.load_generic(params_file)