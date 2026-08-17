import os
from Dapper import calibration

def recalibrate():
    current_folder = os.path.dirname(os.path.abspath(__file__))
    input_data = os.path.join(current_folder, "WallaWalla_OpenAg_2016.csv")

    # use the most recent years
    calibration_years = []
    # for i in range(2015,2023):
    #     calibration_years.append(i)
    calibration_years = [2015]
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

    # Same crop -> value mapping, kept separate in case Etc diverges from
    # elasticity later (right now the values match your input CSV's Etc column)
    etc_values = {
        'Berry': .25,
        'Cereal Grain': .74,
        'Commercial Tree': .13,
        'Flower Bulb / Ornamental': .51,
        'Flower Bulb': .51,
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
    calibrator.apply_to_original = False

    calibrator.calibrate()

    # add Etc column keyed off the crop name column ('i')
    calibrator.calibration_df['Etc'] = calibrator.calibration_df['i'].map(etc_values)

    # save it out to the input file
    calibrator.calibration_df.to_csv(os.path.join(current_folder, "calibration_walla_2016.csv"))


if __name__ == "__main__":
    recalibrate()