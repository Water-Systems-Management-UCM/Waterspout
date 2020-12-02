"""
    This example script uses the Waterspout API to create a single new model run in the application.
    These model runs will be visible to users logging into the web application itself, but this code
    can also be used to retrieve results once they're available.
"""

import itertools
import json
import time

import requests

# the API token is your authentication in here - it identifies you to the application. ask Nick for yours
API_TOKEN = ""
ORGANIZATION_ID = 4  # Your organization identifies where the model runs will be placed and who they'll be available to. DSC's ID is 4
CALIBRATION_SET_ID = 2  # this should be 2 for now, ask Nick and he'll confirm

# set the URL to post model runs to in order to create them in the interface
MODEL_RUN_CREATION_URL = "https://dap.ucmerced.edu/api/model_runs/"
	
land_proportion = 0.0
water_proportion = 0.0
price_proportion = 0.0
yield_proportion = 0.0

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
