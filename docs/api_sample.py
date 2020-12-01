"""
    This example script uses the Waterspout API to create numerous new model runs in the web application.
    These model runs will be visible to users logging into the web application itself, but this code
    can also be used to retrieve results once they're available.
"""

import itertools
import json
import time

import requests

# the API token is your authentication in here - it identifies you to the application. ask Nick for yours
API_TOKEN = ""
ORGANIZATION_ID = 1  # Your organization identifies where the model runs will be placed and who they'll be available to. DSC's ID is 2
CALIBRATION_SET_ID = 1  # this should be 1 for now, ask Nick and he'll confirm

# set the URL to post model runs to in order to create them in the interface
MODEL_RUN_CREATION_URL = "https://dap.ucmerced.edu/api/model_runs/"

# now we're going to use a Python tool to give us every possible combination of 3 values for land/water/price/yield (81 total)
# we'll define the combinations here. The values are the proportion values for each.
LAND_KEY = 0
LAND_OPTIONS = (0.5, 1, 1.2)
WATER_KEY = 1
WATER_OPTIONS = (0.5, 1, 1.2)
PRICE_KEY = 2
PRICE_OPTIONS = (0.8, 1, 1.2)
YIELD_KEY = 3
YIELD_OPTIONS = (0.8, 1, 1.2)

# then get the combinations with itertools.product
permutations = itertools.product(LAND_OPTIONS, WATER_OPTIONS, PRICE_OPTIONS, YIELD_OPTIONS)
# sample results of this are:
#(0.5, 0.5, 0.8, 0.8)
#(0.5, 0.5, 0.8, 1)
#(0.5, 0.5, 0.8, 1.2)
#(0.5, 0.5, 1, 0.8)
#(0.5, 0.5, 1, 1)
#(0.5, 0.5, 1, 1.2)
#(0.5, 0.5, 1.2, 0.8)
#(0.5, 0.5, 1.2, 1)
#(0.5, 0.5, 1.2, 1.2)
# etc

# make a list that we can store results in
model_runs = []
for model_options in permutations:  # loop through every possible permutation

    # start by getting the assigned proportional values for each resource for this iteration/permutation
	land_proportion = model_options[LAND_KEY]
	water_proportion = model_options[WATER_KEY]
	price_proportion = model_options[PRICE_KEY]
	yield_proportion = model_options[YIELD_KEY]
	
    # make a simple name that will be visible in the web application
	model_run_name = 'L{}, W{}, P{}, Y{}'.format(int(land_proportion*100),int(water_proportion*100),int(price_proportion*100),int(yield_proportion*100))
	print("Creating run for {}".format(model_run_name))
    
    # make a region_modifications object
	region_modifications = [{  # make sure to wrap the object(s) in a list as shown here, even if it's only one
		'region': None,  # setting region to None indicates this is the equivalent of the All Regions card settings.
                         # Otherwise you need to know the *integer* region ID from the database (not any other identifier).
                         # You can query the /api/regions endpoint for these, but it'll become more cumbersome. 
		'land_proportion': land_proportion,
		'water_proportion': water_proportion
	},]
	
	crop_modifications = [{
		'crop': None, # same deal as for region modifications. Setting the crop to None indicates this is the equivalent of the All Crops card settings.
                         # Otherwise you need to know the *integer* crop ID from the database (not any other identifier).
                         # You can query the /api/crops endpoint for these, but it'll become more cumbersome. 
        'price_proportion': price_proportion,
        'yield_proportion': yield_proportion,
		'min_land_area_proportion': 0,  # we're just not constraining land area by crop for this example
        'max_land_area_proportion': 2,
	},]
    
	payload_dict = {
        'calibration_set': CALIBRATION_SET_ID,
        'organization': ORGANIZATION_ID,
        'ready': True,  # setting ready to True means that you want the server to process it immediately. If it's False, then you can set it up, get the ID to make changes to later, then set ready to True at another time to begin processing.
        'name': model_run_name,
        'description': "Land Proportion: {}\n, Water Proportion: {}\n, Price Proportion: {}\n, Yield Proportion: {}".format(land_proportion, water_proportion, price_proportion, yield_proportion),  # give it a longer description with the same info as in the name
        'region_modifications': region_modifications,  # assign the modifications to top-level keys - they'll now be nested arrays of objects when we convert to JSON
        'crop_modifications': crop_modifications,
    }
    
    # now send the request to the API, including the proper headers. the json.dumps function turns our model creation parameters into a JSON string for us that can be sent
    # to the server and parsed.
	model_run_details = requests.post(MODEL_RUN_CREATION_URL, data=json.dumps(payload_dict), headers={
        'content-type': 'application/json',  # we have to tell it this so it looks at our attached data s JSON
        'authorization': 'Token {}'.format(API_TOKEN)  # send out authentication information
        })
        
    # print the status code - 201 means it was created, 400 series means various issues (400 means a badly formed request, 401 is a problem with your authentication,
    # but others can mean the request was malformed) and 500-series means that the server-side had an error processing the request. It may be a bad request, but is also a bug worth processing
	print(model_run_details.status_code)
	model_runs.append(model_run_details)  # store the requests object (which includes the ID of the model run so we can retrieve it later) so we can check for results later
    time.sleep(5)  # typically it's nice to APIs to not hit them with requests as fast as possible. Wait 5 seconds before starting the next iteration