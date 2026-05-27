from . import general
from . import core

def load_wa_wallawalla():
	params_file = core.get_data_file_path("wa_wallawalla", "params.json")
	general.load_generic(params_file)