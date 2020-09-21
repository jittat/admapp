from django.conf.urls import url, include
from django.urls import path

from . import views
from criteria.views import criterion

app_name = 'criteria'

urlpatterns = [
    path('', criterion.project_index, {'project_id':1, 'round_id':2}, name='project-index-default'),
    path('<int:project_id>/<int:round_id>/', criterion.project_index, name='project-index'),

    path('<int:project_id>/<int:round_id>/add-major/', criterion.create, name='create'),
]
