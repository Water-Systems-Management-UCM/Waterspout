from rest_framework import serializers

from waterspout_api.models import Region


class RegionSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Region
		fields = ['name', 'internal_id', 'external_id', 'geometry']