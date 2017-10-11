from django.conf.urls import url, include

from . import views
from backoffice.views import projects
from backoffice.views import payments

app_name = 'backoffice'

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^payment/$', payments.index, name='payment-index'),
    
    url(r'^applicants/(\d+)/$', views.show, name='show-applicant'),
    url(r'^applicants/(\d+)/(\d+)/$', views.show, name='show-applicant-in-project'),

    url(r'^search/$', views.search, name='search'),
    url(r'^search/(\d+)/$', views.search, name='search-project'),

    url(r'^projects/(\d+)/(\d+)/$', projects.index, name='projects-index'),
]

