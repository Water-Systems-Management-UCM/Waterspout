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

from rest_framework import routers

from waterspout_api import views as ws_views
from Waterspout.settings import API_URLS

router = routers.DefaultRouter()
router.register(API_URLS["regions"]["partial"], ws_views.RegionViewSet, basename="regions")
router.register(API_URLS["model_runs"]["partial"], ws_views.ModelRunViewSet, basename="model_runs")
router.register(API_URLS["region_modifications"]["partial"], ws_views.RegionModificationViewSet, basename="region_modifications")
router.register(API_URLS["crops"]["partial"], ws_views.CropViewSet, basename="crops")
router.register(API_URLS["users"]["partial"], ws_views.UsersViewSet, basename="users")
router.register(API_URLS["user_profile"]["partial"], ws_views.UserProfileViewSet, basename="user_profile")
router.register(API_URLS["model_areas"]["partial"], ws_views.ModelAreaViewSet, basename="model_areas")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('application-variables/', ws_views.GetApplicationVariables.as_view()),
    path('api/', include(router.urls)),
    path('api-token-auth/', ws_views.CustomAuthToken.as_view()),  # POST a username and password here, get a token back
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('auto-login/', ws_views.AutoLogin.as_view()),
    path('api/reset-password/', ws_views.GetPasswordReset.as_view(), name='password-reset'),
    path('api/password-reset/', ws_views.DoPasswordReset.as_view(), name='password-reset'),
    path('api/password-change/', ws_views.DoPasswordChange.as_view(), name='password-change'),
]
