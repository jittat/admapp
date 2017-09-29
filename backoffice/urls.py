from django.conf.urls import url, include

from . import views

app_name = 'backoffice'

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^applicants/(\d+)/$', views.show, name='show-applicant'),
    url(r'^search/$', views.search, name='search'),
    url(r'^search/(\d+)/$', views.search, name='search-project'),
]

