import json
import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse

from rest_framework import viewsets, renderers, authentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticated, IsAdminUser, SAFE_METHODS
from rest_framework.views import APIView

from Waterspout import settings
from waterspout_api import models
from waterspout_api import serializers
from waterspout_api import support
from waterspout_api import permissions

log = logging.getLogger("waterspout.views")


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
		return Response({
			'token': token.key,
			'user_id': user.pk,
			'username': user.username,
			'is_staff': user.is_staff,
			'is_superuser': user.is_superuser,
			'email': user.email,
		})


class GetApplicationVariables(APIView):
	"""
	View to list all users in the system.

	* Requires token authentication.
	* Only admin users are able to access this view.
	"""
	authentication_classes = [authentication.TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, format=None):
		"""
		Return a list of all users.
		"""

		application_variables = {
		    "model_area_id": 1,
		    "organization_id": 1,
		    "calibration_set_id": 1,
		    "user_api_token": f"{support.get_or_create_token(request.user)}",
		    "api_url_regions": f"{settings.API_URLS['regions']['full']}",
		    "api_url_model_runs": f"{settings.API_URLS['model_runs']['full']}"
		}
		return Response(application_variables)


class RegionViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	permission_classes = [IsAuthenticated]
	serializer_class = serializers.RegionSerializer

	def get_queryset(self):
		return models.Region.objects.filter(model_area__organization__in=support.get_organizations_for_user(self.request.user)).order_by("internal_id")


class RegionModificationViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows modifications to regions to be read and saved
	"""
	permission_classes = [IsAuthenticated]
	serializer_class = serializers.RegionModificationSerializer

	def get_queryset(self):
		return models.RegionModification.objects.filter(model_run__organization__in=support.get_organizations_for_user(self.request.user)).order_by('id')


class PassthroughRenderer(renderers.BaseRenderer):  # we need this so it won't mess with our CSV output and make it HTML
	"""
		Return data as-is. View should supply a Response.
	"""
	media_type = ''
	format = ''
	def render(self, data, accepted_media_type=None, renderer_context=None):
		return data


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

	@action(detail=True, url_name="model_run_csv", renderer_classes=(PassthroughRenderer,))
	def csv(self, request, pk):
		"""
			A temporary proof of concept - allows downloading a csv of model results. Realistically,
			we may want to save these as static files somewhere, but then we'd still want to read
			them in through Django on request to manage permissions. Still would be faster and more
			reliable than making the data frame a CSV on the fly though
		:param request:
		:param pk:
		:return:
		"""
		model_run = self.get_object()  # this checks DRF's permissions here
		if model_run.complete is False:  # if it's not complete, just return the current serialized response - should use the API view instead!
			return Response(json.dumps(model_run))

		output_name = f"waterspout_model_run_{model_run.id}_{model_run.name}.csv"
		response = Response(model_run.results.to_csv(waterspout_limited=True),
		                    headers={'Content-Disposition': f'attachment; filename="{output_name}"'},
		                    content_type='text/csv')
		return response

	@action(detail=True)
	def status_longpoll(self, request, pk):
		"""
			Trying to make something that keeps a longpoll connection
			open, but it's not complete yet.
		:param request:
		:param pk:
		:return:
		"""

		model_run = self.get_object()

		total_time = 0
		while model_run.complete is False or total_time < settings.LONG_POLL_DURATION:
			pass

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

