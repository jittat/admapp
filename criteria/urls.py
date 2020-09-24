from django.conf.urls import url, include
from django.urls import path

from . import views
from criteria.views import criterion

app_name = 'criteria'

urlpatterns = [
    path('', criterion.project_index, {
         'project_id': 1, 'round_id': 2}, name='project-index-default'),
    path('<int:project_id>/<int:round_id>/',
         criterion.project_index, name='project-index'),

    path('<int:project_id>/<int:round_id>/create/',
         criterion.create, name='create'),
    path('<int:project_id>/<int:round_id>/<int:criteria_id>/edit/',
         criterion.edit, name='edit'),
    path('<int:project_id>/<int:round_id>/<int:criteria_id>/delete/',
         criterion.delete, name='delete'),
    path('<int:project_id>/<int:round_id>/curriculum-majors/',
         criterion.select_curriculum_major, name='curriculum-majors'),
    path('<int:project_id>/<int:round_id>/curriculum-majors/toggle/<int:code_id>/<value>/',
         criterion.select_curriculum_major, name='curriculum-majors-toggle'),
]
