from django.urls import re_path, include

from supplements import views

app_name = 'supplements'
urlpatterns = [
    re_path(r'^projects/(\d+)/(\d+)/$', views.index, name='index'),
]
