import copy

from waterspout_api import models

# equivalent to a basic plan - which features are available for anyone with an account?
DEFAULT = {'enforce_price_yield_constraints': True,
		'lock_price_yield_ratio': False,
		'include_net_revenue': False,
		'region_linked_crops': False,
		'allow_model_run_creation_code_view': False,
		'allow_viz_multiple_comparisons': False,
		'allow_viz_normalization': False,
		'allow_viz_region_filter': False,
		'allow_viz_worst_case': False,
		'allow_static_regions': False,
		'allow_removed_regions': False,
}

# the public plan that supports all features
FULL_PUBLIC = copy.deepcopy(DEFAULT)
FULL_PUBLIC['allow_viz_multiple_comparisons'] = True
FULL_PUBLIC['allow_viz_region_filter'] = True
FULL_PUBLIC['allow_viz_normalization'] = True
FULL_PUBLIC['allow_static_regions'] = True
FULL_PUBLIC['allow_removed_regions'] = True

# for internal use
DEBUG = copy.deepcopy(FULL_PUBLIC)
DEBUG['include_net_revenue'] = True
DEBUG['allow_model_run_creation_code_view'] = True

# a few special plans - we'll copy them for now in case they have modifications later
WSDA = copy.deepcopy(FULL_PUBLIC)
DAP_DSC = copy.deepcopy(DEFAULT)
DAP_DSC['allow_removed_regions'] = False


def update_feature_package(model_area):
	preferences = model_area.preferences
	package_name = model_area.feature_package_name

	# get the information for the feature package for this model area
	package = globals()[package_name]
	for key in package:  # for every feature, loop through and set the desired value in the model area's preferences
		setattr(preferences, key, package[key])

	# save the model area preferences
	preferences.save()


def update_all_feature_packages():

	# if we get a larger number of accounts, a better thing to do might be to
	# run models.ModelArea.objects.filter(feature_package_name="some_feature_package_name").update(**the_feature_package_dict)
	# which would keep most of the actions in the DB and run far fewer transactions

	model_areas = models.ModelArea.objects.all()
	for model_area in model_areas:
		update_feature_package(model_area)