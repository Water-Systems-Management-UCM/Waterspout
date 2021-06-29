import json
import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model

from rest_framework import viewsets, renderers, authentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, DjangoObjectPermissions, IsAuthenticated, IsAdminUser, SAFE_METHODS, AllowAny
from rest_framework.views import APIView

from Waterspout import settings
from waterspout_api import models
from waterspout_api import serializers
from waterspout_api import support
from waterspout_api import permissions

log = logging.getLogger("waterspout.views")


def get_user_info_dict(user, token):
	return {
			'token': token,
			'user_id': user.pk,
			'username': user.username,
			'is_staff': user.is_staff,
			'is_superuser': user.is_superuser,
			'email': user.email
		}


class CustomAuthToken(ObtainAuthToken):
	"""
	Via https://www.django-rest-framework.org/api-guide/authentication/
	Creates a custom object that returns more than just the auth token when users hit the API endpoint.
	"""
	def post(self, request, *args, **kwargs):
		serializer = self.serializer_class(data=request.data,
		                                   context={'request': request})
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data['user']
		token, created = Token.objects.get_or_create(user=user)

		return Response(get_user_info_dict(user, token.key))


class GetApplicationVariables(APIView):
	"""
	Get the core variables (basically, dump the URLs that stormchaser should use to e
	* Requires token authentication.
	* Only authenticated users can access
	"""
	authentication_classes = [authentication.TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, format=None):
		"""
		Return a list of all users.
		"""

		# get the user defaults
		group = request.user.groups.first()
		organization = models.Organization.objects.filter(group=group).first()
		model_area = organization.model_areas.first()
		calibration_set = model_area.calibration_data.first()

		application_variables = {
		    "model_area_id": model_area.id,
		    "organization_id": organization.id,
		    "calibration_set_id": calibration_set.id,
			"user_api_token": f"{support.get_or_create_token(request.user)}",
		}
		for url in settings.API_URLS:
			application_variables[f"api_url_{url}"] = settings.API_URLS[url]['full']

		return Response(application_variables)


class AutoLogin(APIView):
	"""
	Returns information about the auto-login ("user-less") system

	"""
	authentication_classes = []
	permission_classes = [AllowAny]

	def get(self, request, format=None):
		"""
		Get the auto login information
		"""

		auto_login_token = None
		user = None
		if settings.AUTO_LOGIN_ENABLED:
			user = get_user_model().objects.get(username=settings.AUTO_LOGIN_USER)
			auto_login_token = f"{support.get_or_create_token(user)}"

		auto_login_info = {
			"auto_login_allowed": settings.AUTO_LOGIN_ENABLED,
			"auto_login_token": auto_login_token,
		}

		if user:
			auto_login_info["user_info"] = get_user_info_dict(user, auto_login_token)

		return Response(auto_login_info)


class UserProfileObjectOnlyPermissions(DjangoObjectPermissions):

	def has_permission(self, request, view):
		# if they provide an "ID", regardless of request method, check their permissions
		# on that userprofile
		if hasattr(request, "data") and "id" in request.data:
			userprofile = models.UserProfile.objects.get(id=request.data['id'])
			return request.user.has_perm('change_userprofile', userprofile)
		# if they don't provide an ID and it's a GET/HEAD, then this will get filtered correctly automatically to their own data in get_queryset
		elif request.method in SAFE_METHODS:
			return True
		# otherwise, they don't have permission
		else:
			return False

class UserProfileViewSet(viewsets.ModelViewSet):
	permission_classes = [UserProfileObjectOnlyPermissions,]  # handles locking it to a particular user
	serializer_class = serializers.UserProfileSerializer

	def get_queryset(self):
		return models.UserProfile.objects.filter(user=self.request.user)


class CropViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	permission_classes = [permissions.IsInSameOrganization]
	serializer_class = serializers.CropSerializer

	def get_queryset(self):
		# this could lead to people getting crops for multiple organizations at the same time. Going to leave it as is for now
		# until we actually have something that sets the currently active organization. Should add that soon
		# should crops also be associated with model areas rather than orgs?? Probably
		return models.Crop.objects.filter(model_area__organization__in=support.get_organizations_for_user(self.request.user)).order_by("name")


class RegionViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	permission_classes = [permissions.IsInSameOrganization]
	serializer_class = serializers.RegionSerializer

	def get_queryset(self):
		return models.Region.objects.filter(model_area__organization__in=support.get_organizations_for_user(self.request.user)).order_by("internal_id")


class RegionModificationViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows modifications to regions to be read and saved
	"""
	permission_classes = [permissions.IsInSameOrganization]
	serializer_class = serializers.RegionModificationSerializer

	def get_queryset(self):
		return models.RegionModification.objects.filter(model_run__organization__in=support.get_organizations_for_user(self.request.user)).order_by('id')


class UsersViewSet(viewsets.ModelViewSet):
	"""
	Returns Users in the same organizations as the current user
	"""
	permission_classes = [IsAuthenticated]
	serializer_class = serializers.UsersSerializer

	# this needs a TEST
	def get_queryset(self):
		# get the groups the user is in
		groups = list(self.request.user.groups.all())

		if len(groups) == 0:
			return None

		# get the queryset for the first user group
		users = groups[0].user_set.all()  # get the first item to start any potential iteration
		if len(groups) == 1:
			return users  # if we only have that group, return it
		else:
			for group in groups[1:]:  # otherwise, iterate through the remaining groups and modify the queryset to include their users
				users = users | group.user_set.all()  # trying to make Django do the work so we don't eval the queryset until we're done getting all of them

		return users.distinct()  # now that we've joined the querysets, as for only the distinct users


class CropModificationViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows modifications to regions to be read and saved
	"""
	permission_classes = [permissions.IsInSameOrganization]
	serializer_class = serializers.CropModificationSerializer

	def get_queryset(self):
		return models.CropModification.objects.filter(model_run__organization__in=support.get_organizations_for_user(self.request.user)).order_by('id')


class PassthroughRenderer(renderers.BaseRenderer):  # we need this so it won't mess with our CSV output and make it HTML
	"""
		Return data as-is. View should supply a Response.
	"""
	media_type = ''
	format = ''
	def render(self, data, accepted_media_type=None, renderer_context=None):
		return data


class ModelAreaViewSet(viewsets.ModelViewSet):
	permission_classes = [permissions.IsInSameOrganization]
	serializer_class = serializers.ModelAreaSerializer

	def get_queryset(self):
		return models.ModelArea.objects.filter(organization__in=support.get_organizations_for_user(self.request.user)).order_by('id')

	@action(detail=True, url_name="get_model_runs", )
	def model_runs(self, request, pk):
		mrs = models.ModelRun.objects.filter(
			calibration_set__model_area__id=pk,
			organization__in=support.get_organizations_for_user(self.request.user)
		).order_by('id')

		serializer = serializers.ModelRunSerializer(mrs, many=True)
		return Response(serializer.data)


class ModelRunViewSet(viewsets.ModelViewSet):
	"""
	Create, List, and Modify Model Runs

	Test

	Permissions: Must be in same organization to specifically request an item
	"""
	permission_classes = [permissions.IsInSameOrganization]
	serializer_class = serializers.ModelRunSerializer

	def get_queryset(self):
		# right now, this will only show the user's model runs, not the organization's,
		# but permissions should be saying "
		return models.ModelRun.objects.filter(organization__in=support.get_organizations_for_user(self.request.user)).order_by('id')

	# Commented out 11/28/2020 - no longer using back end to generate CSVs through stormchaser
	#@action(detail=True, url_name="model_run_csv", renderer_classes=(PassthroughRenderer,))
	#def csv(self, request, pk):
	#	"""
	#		A temporary proof of concept - allows downloading a csv of model results. Realistically,
	#		we may want to save these as static files somewhere, but then we'd still want to read
	#		them in through Django on request to manage permissions. Still would be faster and more
	#		reliable than making the data frame a CSV on the fly though
	#	:param request:
	#	:param pk:
	#	:return:
	#	"""
	#	model_run = self.get_object()  # this checks DRF's permissions here
	#	if model_run.complete is False:  # if it's not complete, just return the current serialized response - should use the API view instead!
	#		return Response(json.dumps(model_run))
	#
	#	output_name = f"waterspout_model_run_{model_run.id}_{model_run.name}.csv"
	#	response = Response(model_run.results.to_csv(waterspout_limited=True, waterspout_sort_columns=False),
	#	                    headers={'Content-Disposition': f'attachment; filename="{output_name}"'},
	#	                    content_type='text/csv')
	#	return response

	#@action(detail=True)
	#def status_longpoll(self, request, pk):
	#	"""
	#		Trying to make something that keeps a longpoll connection
	#		open, but it's not complete yet.
	#	:param request:
	#	:param pk:
	#	:return:
	#	"""
	#
	#	model_run = self.get_object()
	#
	#	total_time = 0
	#	while model_run.complete is False or total_time < settings.LONG_POLL_DURATION:
	#		pass

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

	#def create(self, request, *args, **kwargs):
	#	# check the permissions using the request before sending it off to the serializer
	#	request.data = self._check_permissions(request)

	#	super().create(request, *args, **kwargs)


@login_required()
def stormchaser_variable_only(request):
	"""
		Returns Stormchaser JSON values and a token - there's a simpler
		way to do it, but we already have some of these variables defined in
		a way that makes them available in a template - this works during
		development, but we'll want to move to something better in the long
		run, I think.
	:param request:
	:return:
	"""
	user = request.user
	token = support.get_or_create_token(user).key  # will be the logged in user's token - send it to the template so the app can use it
	return render(request, "waterspout_api/stormchaser_json.django.html", {"USER_API_TOKEN": token}, content_type="application/json")

