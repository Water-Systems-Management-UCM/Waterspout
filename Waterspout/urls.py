"""Waterspout URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url

from rest_framework import routers

from waterspout_api import views as ws_views
from Waterspout.settings import API_URLS

router = routers.DefaultRouter()
router.register(API_URLS["regions"]["partial"], ws_views.RegionViewSet)
router.register(API_URLS["model_runs"]["partial"], ws_views.ModelRunViewSet, basename="model_runs")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('stormchaser/', ws_views.stormchaser),
    path('api/', include(router.urls)),
    url(r'^api-token-auth/', ws_views.CustomAuthToken.as_view()),  # POST a username and password here, get a token back
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
