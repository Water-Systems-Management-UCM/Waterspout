import os
from Dapper import calibration

def recalibrate():
	current_folder = os.path.dirname(os.path.abspath(__file__))
	input_data = os.path.join(current_folder, "OpenAgWA_consolidated_Annual_02152021.csv")

	# use the most recent years
	calibration_years = [2016, 2017, 2018]

	# temporary value - checked this price with Spencer and Alvar - will update
	price_of_water = 15

	# Rough set of elasticities from Alvar 4/2/2021 - may need updating, but should be decent
	elasticities = {
		'ALFALFA': 0.51,
		'BEAN': 0.17,
		'GRAIN': 0.38,
		'PEA': 0.17,
		'WHEAT': 0.38,
		'APPLE': 0.11,
		'CHERRY': 0.11,
		'CORN': 0.45,
		'HAY': 0.51,
		'CANEBERRY': 0.11,
		'BLUEBERRY': 0.11,
		'GRAPE': 0.11,
		'HOPS': 0.2,
		'PASTURE': 0.51,
		'PEAR': 0.11,
		'POTATO': 0.19,
		'VEGETABLE': 0.3
	}

	calibrator = calibration.ModelCalibration(
		initial_data=input_data,
		crop_elasticities=elasticities,
		price_of_water=price_of_water,
		calibration_years=calibration_years
	)
	# give me one record per crop/region, not one record per input record (year)
	calibrator.apply_to_original = False

	calibrator.calibrate()

	# save it out to the input file
	calibrator.calibration_df.to_csv(os.path.join(current_folder, "WA_DAP_format_calibrated.csv"))


if __name__ == "__main__":
	recalibrate()