from django.conf.urls import url, include

from . import views

app_name = 'regis'

urlpatterns = [
    url(r'^register/$', views.register, name='register'),
    url(r'^forget/$', views.forget, name='forget'),

    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),

    url(r'^checkcupt/(\d+)/$', views.check_cupt_confirmation_available, name='cupt-check'),

    url(r'^resetcupt/$', views.reset_cupt_confirmation, name='reset-cupt-check'),

    url(r'^log/$', views.save_applicant_log, name='save-applicant-log'),
]
