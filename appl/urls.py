from django.conf.urls import url, include

from appl import views
from appl.views import upload as upload_views

app_name = 'appl'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^upload/(\d+)/$', upload_views.upload, name='upload'),
]

