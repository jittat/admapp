from django.conf.urls import url, include

from . import views

app_name = 'qrconfirmations'

urlpatterns = [
    url(r'^health/$', views.health, name='health'),
    url(r'^sent/$', views.sent, name='sent'),
    url(r'^confirm/(?P<transaction_id>\d+)/$', views.confirm, name='confirm'),
]

