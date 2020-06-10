from rest_framework.authtoken.models import Token


def refresh_token_for_user(user):
	"""
		Deletes *all* existing tokens for the user specified, creates a new token, saves it,
		and returns it to the caller
	:param user: a Django User object
	:return: a DRF Token object. The actual token string is the "key" attribute on it
	"""
	# get rid of any current tokens
	Token.objects.filter(user=user).delete()

	new_token = Token.objects.create(user=user)
	new_token.save()
	return new_token


def get_or_create_token(user):
	"""
		Gets the current token for a user, and if no token exists, creates one. If one already exists,
		returns it. If you want to force a new token (and essentially a logout of all existing
		tokens for the user), just use `refresh_token_for_user` instead.
	:param user: a Django User object
	:return: a DRF Token object. The actual token string is the "key" attribute on it
	:return:
	"""
	tokens = Token.objects.filter(user=user)
	if len(tokens) == 0:
		return refresh_token_for_user(user)
	else:
		return tokens.first()
