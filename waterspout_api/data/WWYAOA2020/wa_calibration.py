import os
from Dapper import calibration

def recalibrate():
    current_folder = os.path.dirname(os.path.abspath(__file__))
    input_data = os.path.join(current_folder, "inputdata_2020.csv")

    # use the most recent years
    calibration_years = [2020]
    # for i in range(2015,2025):
    #     calibration_years.append(i)

    # temporary value - checked this price with Spencer and Alvar - will update
    price_of_water = 15

    # Rough set of elasticities from Alvar 4/2/2021 - may need updating, but should be decent
    elasticities = {
        'Berry': .25,
        'Cereal Grain': .74,
        'Commercial Tree': .13,
        'Flower Bulb / Ornamental': .51,
        'Green Manure': .41,
        'Hay/Silage': .51,
        'Herb': .41,
        'Oilseed': .74,
        'Seed': .74,
        'Orchard': .13,
        'Pasture': .51,
        'Turfgrass / Specialty': .51,
        'Vegetable': .3,
        'Vineyard': .13
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
    calibrator.calibration_df.to_csv(os.path.join(current_folder, "calibration_data2020.csv"))


if __name__ == "__main__":
    recalibrate()