from django.urls import re_path

from . import views

app_name = 'regis'

urlpatterns = [
    re_path(r'^register/$', views.register, name='register'),
    re_path(r'^forget/$', views.forget, name='forget'),

    re_path(r'^login/$', views.login, name='login'),
    re_path(r'^logout/$', views.logout, name='logout'),

    re_path(r'^checkcupt/(\d+)/$', views.check_cupt_confirmation_available, name='cupt-check'),

    re_path(r'^resetcupt/$', views.reset_cupt_confirmation, name='reset-cupt-check'),

    re_path(r'^log/$', views.save_applicant_log, name='save-applicant-log'),
]
