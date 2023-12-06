import json

from . import core

# We're slowly moving toward a more general loader. It's not
# been entirely clear what our target is. We designed for a
# broader range of data than we had, but we're still getting
# changes in new datasets, so it's been hard to pin down
# a single loader that didn't need custom code. Working our way
# there.

def load_generic(params_file):
	with open(params_file, 'r') as params_json:
		params = json.load(params_json)

	if "mapping" in params:  # our default loading code expects these things to be flat, but nicer to configure as a unit to make it clearer
		for key in params["mapping"]:
			params[key] = params["mapping"][key]

	if "features" in params:
		# this might be temporary, but the dap_style_inputs loader doesn't take these kwargs
		# it may be that we need a reworked version that does because these features will probably
		# be needed there
		features = params["features"]

	model_area = core.load_dap_style_inputs(**params)

	if params["preload_model_run_results"]:
		core.preload_model_runs(params["preload_model_run_results"]["files"], data_name=params["data_name"], model_area=model_area)

	model_area