import sys
import os
import subprocess

import requests

BASE_URL = "https://wsm-ucm-dapper.s3-us-west-1.amazonaws.com/"

if sys.platform == "win32":
	EXTENSION = "-win_amd64.whl.txt"
elif sys.platform == "linux":
	EXTENSION = "-linux_x86_64.whl.txt"
else:
	raise NotImplementedError(f"Platform {sys.platform} is not supported")

version_string = f"{sys.version_info.major}{sys.version_info.minor}"
full_url = f"{BASE_URL}latest_cp{version_string}-cp{version_string}m{EXTENSION}"
# sometimes we don't have an "m" after the second version string, so we might try a version without it.
alternate_full_url = f"{BASE_URL}latest_cp{version_string}-cp{version_string}{EXTENSION}"


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

# not my best code, but simple, clear, and works
if r.status_code not in (200, 201):  # if we don't get an "OK" response, try the alternate URL
	print("First attempt failed, trying alternate URL")
	r = requests.get(url=alternate_full_url)
	if r.status_code not in (200, 201):
		raise RuntimeError("Can't find latest version of Dapper via {} or {}".format(full_url, alternate_full_url))

wheel_url = f"{BASE_URL}{r.content.decode('utf-8')}"
print("Downloading wheel at {}".format(wheel_url))
wheel_filename = download_file(url=wheel_url)
print("Installing wheel")
subprocess.check_call([sys.executable, '-m', 'pip', 'install', wheel_filename])
print("Removing wheel file")
os.remove(wheel_filename)  # clean up now