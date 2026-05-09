from django.contrib import admin
from django.urls import path

from route_api.views import (

    home,

    FuelRouteAPIView,

    LocationSuggestionAPIView
)

urlpatterns = [

    # Frontend home page
    path(
        '',
        home
    ),

    # Django admin panel
    path(
        'admin/',
        admin.site.urls
    ),

    # Main fuel route API
    path(
        'api/route/',
        FuelRouteAPIView.as_view()
    ),

    # Location suggestions API
    path(
        'api/suggestions/',
        LocationSuggestionAPIView.as_view()
    ),
]