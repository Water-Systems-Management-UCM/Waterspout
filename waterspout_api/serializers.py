from rest_framework import serializers

from waterspout_api import models


class RegionSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = models.Region
		fields = ['name', 'internal_id', 'external_id', 'geometry']


class ModelRunSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = models.ModelRun
		fields = ['id', 'ready', 'running', 'complete', 'status_message',
		          'date_submitted', 'date_completed', "calibrated_parameters_text",]