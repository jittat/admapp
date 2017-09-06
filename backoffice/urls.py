from django.conf.urls import url, include

from . import views

app_name = 'backoffice'

urlpatterns = [
    url(r'^$', views.index, name='index'),
]

