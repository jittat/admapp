from django.conf.urls import url, include

from supplements import views

app_name = 'supplements'
urlpatterns = [
    url(r'^projects/(\d+)/$', views.index, name='index'),
]
