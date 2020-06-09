from django.shortcuts import render

from rest_framework import viewsets
# Create your views here.

from waterspout_api.models import Region
from waterspout_api.serializers import RegionSerializer


class RegionViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = Region.objects.all().order_by("internal_id")
	serializer_class = RegionSerializer


def stormchaser(request):
	return render(request, "waterspout_api/stormchaser.django.html")


