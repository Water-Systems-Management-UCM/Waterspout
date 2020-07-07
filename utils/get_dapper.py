import sys
import os
import subprocess

import requests

BASE_URL = "https://wsm-ucm-dapper.s3-us-west-1.amazonaws.com/"
EXTENSION = "-linux_x86_64.whl.txt"

version_string = f"{sys.version_info.major}{sys.version_info.minor}"
full_url = f"latest_{BASE_URL}cp{version_string}-cp{version_string}m{EXTENSION}"


def download_file(url):
	"""
		Retrieves a file from the web and keeps its name locally
		Adapted from http://stackoverflow.com/questions/16694907/ddg#16696317
	:param url:
	:return:
	"""
	local_filename = url.split('/')[-1]
	r = requests.get(url, stream=True)
	with open(local_filename, 'wb') as f:
		for chunk in r.iter_content(chunk_size=1024):
			if chunk:  # filter out keep-alive new chunks
				f.write(chunk)
	return local_filename

print("Retrieving info on latest version from {}".format(full_url))
r = requests.get(url=full_url)
wheel_url = f"{BASE_URL}{str(r.content)}"
print("Downloading wheel at {}".format(wheel_url))
wheel_filename = download_file(url=wheel_url)
print("Installing wheel")
subprocess.check_call([sys.executable, '-m', 'pip', 'install', wheel_filename])
print("Removing wheel file")
os.remove(wheel_filename)  # clean up now