from django.conf.urls import url, include

from form import views

app_name = 'form'
urlpatterns = [
	url(r'^$', views.education_form, name='education_form'),
]