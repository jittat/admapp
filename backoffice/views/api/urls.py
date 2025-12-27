from django.urls import path
from django.urls import re_path, include

from backoffice.views import api

urlpatterns = [
    path("projects/", api.projects, name="api-projects"),
]
