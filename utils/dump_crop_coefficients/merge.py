import os

import pandas

from .website_data import CROPS, STATIONS
from .dump import get_print_id

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))

stations = {}
# start by making sure the STATIONS dict has entries for all of our stations
for station in STATIONS: # this will create duplicates whenever stations had hyphens, but it's only a lookup now so it's OK
	stations[get_print_id(station)] = STATIONS[station]


def merge_csvs(crops=CROPS, stations=stations, efficiencies=(100,), folder=os.path.join(BASE_FOLDER, "raw_results")):
	data_frames = []  # we'll store them here and then concatenat them in one go for efficiency0
	for crop in crops:
		print(crop)
		crop_folder = os.path.join(folder, crop)
		for station in stations:
			for efficiency in efficiencies:
				file_path = os.path.join(crop_folder, f"{crop}_{station}_{efficiency}.csv")
				if not os.path.exists(file_path): # they might not exist because we've duplicated stations with hyphens in the ID
					continue

				df = pandas.read_csv(file_path)
				df["station_name"] = stations[station]
				df["station_id"] = station
				df["efficiency"] = efficiency
				df["crop_id"] = crop
				df["crop_name"] = crops[crop]
				data_frames.append(df)

	final_df = pandas.concat(data_frames, ignore_index=True)
	final_df.to_csv(os.path.join(folder, "merged_results.csv"))
