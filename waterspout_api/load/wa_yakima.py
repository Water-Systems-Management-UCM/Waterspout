from . import general
from . import core

def load_wa_yakima():
	params_file = core.get_data_file_path("wa_yakima", "params.json")
	general.load_generic(params_file)