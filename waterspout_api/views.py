import json
import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticated, IsAdminUser, SAFE_METHODS
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import status

from waterspout_api import models
from waterspout_api import serializers
from waterspout_api import support
from Waterspout import settings

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


class RegionViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	permission_classes = [IsAuthenticated]
	queryset = models.Region.objects.all().order_by("internal_id")
	serializer_class = serializers.RegionSerializer


class ModelRunViewSet(viewsets.ModelViewSet):
	"""
	Create, List, and Modify Model Runs

	Test

	Permissions: Must be authenticated
	"""
	permission_classes = [IsAuthenticated]
	serializer_class = serializers.ModelRunSerializer

	def get_queryset(self):
		return models.ModelRun.objects.filter(user=self.request.user).order_by('id')

	def _check_permissions(self, request):
		request_data = json.loads(request.data)

		log.debug(f"Make Model Run Request: ${request_data}")

		# Check Permissions
		organization = models.Organization.objects.get(id=int(request_data["organization"]))
		if not organization.has_member(request.user):
			raise PermissionDenied("User is not a member of the specified organization and cannot create model runs within it")
		request_data["organization"] = organization  # replace it with the object so we can assign it later

		calibration_set = models.CalibrationSet.objects.get(id=int(request_data["calibration_set"]))
		log.debug(f"Calibration Set: {calibration_set}")
		if not calibration_set.model_area.organization == organization:
			raise PermissionDenied(detail="CalibrationSet is not part of this organization. You can only use calibration sets that"
			                              "are attached to the organization you're working within")
		request_data["calibration_set"] = calibration_set  # replace it with the object so we can assign it later

		return request_data

	def create(self, request, *args, **kwargs):
		request_data = self._check_permissions(request)

		# we could override perform_create instead of create, but we don't get the full
		# request data in perform_create, so we'd probably need to override create *and*
		# perform_create, then call the superclass's create when we're done with our
		# permissions checks.

		try:
			mr = models.ModelRun(
				user=request.user,  # user will be authenticated by permission classes,
				**request_data
			)
			mr.full_clean()
		except:
			if settings.DEBUG:
				raise
			raise ValidationError(detail="Invalid parameters to create model run")

		mr.save()

		# The following code comes from DRF directly and is how it returns the model
		# after creation
		return Response(mr.as_json(), status=status.HTTP_201_CREATED)


@login_required
def stormchaser(request):
	user = request.user
	token = support.get_or_create_token(user).key  # will be the logged in user's token - send it to the template so the app can use it
	return render(request, "waterspout_api/stormchaser.django.html", {"USER_API_TOKEN": token})


