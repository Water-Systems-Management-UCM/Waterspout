from Waterspout.settings import API_URLS


def api_urls(request):
	"""
		Provides all items from the API URLs settings object as variables available in Django Templates
	:param request:
	:return:
	"""
	# make a new dictionary that returns any defined full API URL - does not include any
	# item where the value is None because that needs to be translated to "null" for JS

	# dictionary comprehension that flattens the API_URLS from settings, providing only non-null
	# values of the "full" url.
	return {
		f"API_URLS_{key}": API_URLS[key]["full"] for key in API_URLS if API_URLS[key] is not None
	}
