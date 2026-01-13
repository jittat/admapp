from django.urls import path
from django.urls import re_path, include

from backoffice.views import api

urlpatterns = [
    path("projects/", api.projects, name="api-projects"),
    path("applicants/<int:admission_round_id>/", api.applicants, name="api-applicants-all"),
    path("applicants/<int:admission_round_id>/<int:project_id>/", api.applicants, name="api-applicants"),

    path("slots/<int:year>/", api.admission_slot_stats, name="api-stats")
]
