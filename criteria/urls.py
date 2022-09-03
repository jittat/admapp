from django.conf.urls import url, include
from django.urls import path

from . import views

app_name = 'criteria'

urlpatterns = [
    path('<int:project_id>/<int:round_id>/',
         views.project_index, name='project-index'),

    path('<int:project_id>/<int:round_id>/create/',
         views.create, name='create'),
    path('<int:project_id>/<int:round_id>/<int:criteria_id>/edit/',
         views.edit, name='edit'),
    path('<int:project_id>/<int:round_id>/<int:criteria_id>/delete/',
         views.delete, name='delete'),

    path('<int:project_id>/<int:round_id>/curriculum-majors/',
         views.select_curriculum_majors, name='curriculum-majors'),
    path('<int:project_id>/<int:round_id>/curriculum-majors/toggle/<int:code_id>/<value>/',
         views.select_curriculum_majors, name='curriculum-majors-toggle'),

    path('curriculum-majors/',
         views.list_curriculum_majors, name='list-curriculum-majors'),

    path('report/<int:project_id>/<int:round_id>/',
         views.project_report, name='project-report'),

    path('<int:project_id>/<int:round_id>/addlimit/<int:mid>/',
         views.update_add_limit, name='update_add_limit'),
    path('<int:project_id>/<int:round_id>/currtype/<int:acid>/<int:ctypeid>/',
         views.update_accepted_curriculum_type, name='update_accepted_curriculum_type'),
]
