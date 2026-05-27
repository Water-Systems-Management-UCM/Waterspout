from . import general
from . import core

def load_calvin_cvpm():
	params_file = core.get_data_file_path("calvin_cvpm", "params.json")
	general.load_generic(params_file)