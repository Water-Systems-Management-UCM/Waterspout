from . import general
from . import core


def load_ca_cv_drought():
    params_file = core.get_data_file_path("ca_cv_drought", "params.json")
    general.load_generic(params_file)
