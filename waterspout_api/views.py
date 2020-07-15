import json
import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticated, IsAdminUser, SAFE_METHODS

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


class RegionViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	permission_classes = [IsAuthenticated]
	queryset = models.Region.objects.all().order_by("internal_id")
	serializer_class = serializers.RegionSerializer


class RegionModificationViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	permission_classes = [IsAuthenticated]
	queryset = models.RegionModification.objects.all().order_by("internal_id")
	serializer_class = serializers.RegionModificationSerializer


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
		return models.ModelRun.objects.filter(user=self.request.user).order_by('id')

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

	#def create(self, request, *args, **kwargs):
	#	# check the permissions using the request before sending it off to the serializer
	#	request.data = self._check_permissions(request)

	#	super().create(request, *args, **kwargs)


@login_required
def stormchaser(request):
	user = request.user
	token = support.get_or_create_token(user).key  # will be the logged in user's token - send it to the template so the app can use it
	return render(request, "waterspout_api/stormchaser.django.html", {"USER_API_TOKEN": token})


