from django.conf.urls import url, include
from django.urls import path

from . import views
from criteria.views import criterion

app_name = 'criteria'

urlpatterns = [
    path('<int:project_id>/<int:round_id>/',
         criterion.project_index, name='project-index'),

    path('<int:project_id>/<int:round_id>/create/',
         criterion.create, name='create'),
    path('<int:project_id>/<int:round_id>/<int:criteria_id>/edit/',
         criterion.edit, name='edit'),
    path('<int:project_id>/<int:round_id>/<int:criteria_id>/delete/',
         criterion.delete, name='delete'),

    path('<int:project_id>/<int:round_id>/curriculum-majors/',
         criterion.select_curriculum_majors, name='curriculum-majors'),
    path('<int:project_id>/<int:round_id>/curriculum-majors/toggle/<int:code_id>/<value>/',
         criterion.select_curriculum_majors, name='curriculum-majors-toggle'),

    path('curriculum-majors/',
         criterion.list_curriculum_majors, name='list-curriculum-majors'),

    path('report/<int:project_id>/<int:round_id>/',
         criterion.project_report, name='project-report'),
]
