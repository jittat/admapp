from django.conf.urls import url, include
from django.urls import path

from . import views
from criteria.views import criterion

app_name = 'criteria'

urlpatterns = [
    url(r'^$', criterion.index, name='criterion-index'),
    url(r'^(\d+)/(\d+)/add-major$', criterion.create, name='criterion-create'),
]
