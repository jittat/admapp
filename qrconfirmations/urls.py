from django.urls import re_path, include

from . import views

app_name = 'qrconfirmations'

urlpatterns = [
    re_path(r'^health/$', views.health, name='health'),
    re_path(r'^sent/$', views.sent, name='sent'),
    re_path(r'^confirm/(?P<transaction_id>\d+)/$', views.confirm, name='confirm'),
]

