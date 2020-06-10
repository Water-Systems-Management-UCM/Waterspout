from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets
# Create your views here.

from waterspout_api.models import Region
from waterspout_api.serializers import RegionSerializer
from waterspout_api import support


class RegionViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = Region.objects.all().order_by("internal_id")
	serializer_class = RegionSerializer

@login_required
def stormchaser(request):
	user = request.user
	token = support.get_or_create_token(user).key  # will be the logged in user's token - send it to the template so the app can use it
	return render(request, "waterspout_api/stormchaser.django.html", {"USER_API_TOKEN": token})


