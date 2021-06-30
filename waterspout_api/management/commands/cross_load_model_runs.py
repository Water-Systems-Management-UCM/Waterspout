import logging
import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from waterspout_api import models

log = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Loads data from one waterspout server to another. Must have already set up the full model area and user accounts, but creates model runs that match inputs on other server'

	def add_arguments(self, parser):
		parser.add_argument('--remote_api_address', type=str, dest="remote_api_address", default=None,)
		parser.add_argument('--remote_area_id', type=int, dest="remote_area_id", default=None,)
		parser.add_argument('--remote_token', type=str, dest="remote_token", default=None,)
		parser.add_argument('--local_area_id', type=int, dest="local_area_id", default=None,)
		parser.add_argument('--user_id_map', nargs='*', type=str, dest="user_id_map", default=None,)
		parser.add_argument('--system_user_id', type=int, dest="system_user_id", default=None,)
		parser.add_argument('--ignore_run_ids', nargs='*', type=int, dest="ignore_run_ids", help="A space separated list of run IDs on the remote server to ignore - recommended to include the base case here since it'll already be loaded", default=None,)
		parser.add_argument('--dry_run', type=bool, dest="dry_run", required=False)

	def get_user_id_dict(self, user_id_data):
		"""
			User ID Map data is an array of remote_server_id:local_server_id
		:param user_id_data:
		:return:
		"""
		lookup_dict = {}
		for item in user_id_data:
			remote_id, local_id = item.split(":")
			lookup_dict[int(remote_id)] = int(local_id)

		return lookup_dict

	@transaction.atomic
	def handle(self, *args, **options):
		log.info("Loading data to database")

		log.info("Options")
		log.info(f"Dry Run: {options['dry_run']}")
		log.info(f"Ignore Run IDs: {options['ignore_run_ids']}")
		log.info(f"User ID Map: {options['user_id_map']}")

		user_id_lookup_dict = self.get_user_id_dict(options["user_id_map"])

		# look up system user and check that its name is system to confirm its correct - let it fail if it can't find
		# a matching user.
		models.User.objects.filter(username="system", id=options["system_user_id"]).exists()

		auth_headers = {"authorization": f"Token {options['remote_token']}", "content-type": "application/json"}

		# connect to remote API's model area and get just the model area info with regions, etc
		# create a region id lookup, where we get the local IDs that match the remote region IDs by looking up
		# the regions in the local model area by internal id
		model_area_raw = requests.get(
			f"{options['remote_api_address']}model_areas/{options['remote_area_id']}",
			headers=auth_headers
		)
		model_area_data = model_area_raw.json()

		regions = model_area_data["region_set"]
		crops = model_area_data["crop_set"]

		local_model_area = models.ModelArea.objects.get(id=options["local_area_id"])

		region_id_lookup = {}
		# make sure regions with the same internal ID exist and make a lookup
		for region in regions:
			# we want this to fail if we can't find it - we shouldn't proceed if the model areas don't match
			local_region = models.Region.objects.get(internal_id=region["internal_id"], model_area=local_model_area)
			region_id_lookup[region["id"]] = local_region.id

		# do the same thing with crops
		crop_id_lookup = {}
		# make sure crops with the same internal ID exist and make a lookup
		for crop in crops:
			# we want this to fail if we can't find it - we shouldn't proceed if the model areas don't match
			local_crop = models.Crop.objects.get(crop_code=crop["crop_code"], model_area=local_model_area)
			crop_id_lookup[crop["id"]] = local_crop.id

		# connect to url using remote token and get list of model runs
		model_runs_raw = requests.get(
			f"{options['remote_api_address']}model_areas/{options['remote_area_id']}/model_runs",
			headers=auth_headers
		)
		model_runs = model_runs_raw.json()

		# start cross-loading data one by one
		for remote_run in model_runs:
			if remote_run["id"] in options["ignore_run_ids"]:
				log.info(f"skipping run {remote_run['id']} because it is in 'ignore_run_ids'")
				continue

			new_run = models.ModelRun()
			log.info(f"Creating model run {remote_run['name']}")
			new_run.name = remote_run["name"]
			new_run.ready = True
			new_run.description = remote_run["description"]
			new_run.date_submitted = remote_run["date_submitted"]
			new_run.calibration_set = local_model_area.calibration_data.first()
			new_run.rainfall_set = local_model_area.rainfall_data.first()

			if remote_run['user_id'] in user_id_lookup_dict:
				user_id = user_id_lookup_dict[remote_run['user_id']]
			else:
				user_id = options["system_user_id"]
			new_run.user_id = user_id

			new_run.organization = local_model_area.organization

			if not options["dry_run"]:
				new_run.save()

			for remote_mod in remote_run["region_modifications"]:
				log.info(f"Creating region modification for region {remote_mod['region']}")
				region_mod = models.RegionModification()
				region_mod.water_proportion = remote_mod["water_proportion"]
				region_mod.land_proportion = remote_mod["land_proportion"]
				region_mod.rainfall_proportion = remote_mod["rainfall_proportion"]
				region_mod.modeled_type = remote_mod["modeled_type"]

				if remote_mod['region'] is None:
					region_mod.region_id = None
				else:
					region_mod.region_id = region_id_lookup[remote_mod['region']]

				if not options["dry_run"]:
					region_mod.model_run = new_run
					region_mod.save()

			for remote_mod in remote_run["crop_modifications"]:
				log.info(f"Creating crop modification for crop {remote_mod['crop']}")
				crop_mod = models.CropModification()
				crop_mod.price_proportion = remote_mod["price_proportion"]
				crop_mod.yield_proportion = remote_mod["yield_proportion"]
				crop_mod.min_land_area_proportion = remote_mod["min_land_area_proportion"]

				max_land = remote_mod["max_land_area_proportion"]
				if max_land is not None and max_land <= 0.001:  # if we have a zero value for the max_land, that's likely an error - shouldn't be possible
					max_land = None
				crop_mod.max_land_area_proportion = max_land

				# set the region relationship
				if remote_mod['region'] is None:
					crop_mod.region_id = None
				else:
					crop_mod.region_id = region_id_lookup[remote_mod['region']]

				# now set the crop relationship
				if remote_mod['crop'] is None:
					crop_mod.crop_id = None
				else:
					crop_mod.crop_id = crop_id_lookup[remote_mod['crop']]

				if not options["dry_run"]:
					crop_mod.model_run = new_run
					crop_mod.save()



