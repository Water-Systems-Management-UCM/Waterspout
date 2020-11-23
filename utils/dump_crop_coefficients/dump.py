import os
import time

import requests

# data from the page
from .website_data import CROPS, STATIONS

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))

# we'll make a request to MAIN_URL to start a session (PHPSESSID cookie), then proceed between the other two
MAIN_URL = r"http://irrigation.wsu.edu/Content/Calculators/Historic/ajax/StationCrop5Stage.class.php"
CSV_URL = r"http://irrigation.wsu.edu/Content/Calculators/Historic/CsvOutput.php"

# what irrigation efficiencies should we retrieve?
EFFICIENCIES = (100,)


def initialize_session(url=MAIN_URL):
	response = requests.post(url)
	return response.cookies


def get_print_id(id):
	"""
		Some of the ids have the name in them still - we'll parse it out if we see it to make things a bit more consistent
		in our naming
	:param id:
	:return:
	"""
	if "-" in id:  # the ones with the ID are split by hyphens
		return id.split("-")[0].rstrip()  # split it by hyphen, get the first item, then remove trailing whitespace
	else:
		return id


def dump_data(stations=STATIONS,
				crops=CROPS,
				efficiencies=EFFICIENCIES,
				main_url=MAIN_URL,
				csv_url=CSV_URL,
				output_folder=os.path.join(BASE_FOLDER, "raw_results"),
				skip_existing=True):
	"""
		:param stations: dictionary with station IDs as the keys and names as values
		:param crops: dictionary with crop IDs as the keys and names as the values
		:param efficiencies: iterable of percent efficiencies
		:param main_url:
		:param csv_url:
		:param output_folder: the base folder to output all the CSVs to - it'll make a per-crop subfolder
		:param skip_existing: If an output for the current crop/station exists in the output folder, then don't
				try to download it again - useful for resuming
		:return:
	"""

	cookies = initialize_session(main_url)

	# we could structure this differently, but nested for loops will be fine

	for crop_id in crops:  # fewer crops - using them as the outer lets us monitor progress better by just printing their ID
		print(f"Crop: {crop_id} - {crops[crop_id]}")

		# make an output folder for each crop so we don't fill one folder with 17k small files
		crop_output_folder = os.path.join(output_folder, crop_id)
		os.makedirs(crop_output_folder, exist_ok=True)

		for station_id in stations:
			for efficiency in efficiencies:
				output_name = f"{crop_id}_{get_print_id(station_id)}_{efficiency}.csv"
				output_path = os.path.join(crop_output_folder, output_name)
				if os.path.exists(output_path) and skip_existing:  # if we have it and want to skip, then skip
					continue

				# otherwise, make the request for the params - we don't need to save it, just need to set up their
				# system for us to request the CSV without params
				requests.post(main_url, {'cropID': crop_id, 'stationID': station_id, 'efficiency': efficiency}, cookies=cookies)

				# then get the CSV - it comes back in the content attribute
				csv_data = requests.post(csv_url, cookies=cookies).content

				with open(output_path, 'wb') as output_fh:
					lines = b"\n".join(csv_data.split(b"\n")[9:])  # split by newline, remove the first 9 (header info), then rejoin them with a newline
					output_fh.write(lines)

				time.sleep(2)  # be courteous to their server - this is still somewhat aggressive, but we have 17,000 combinations
