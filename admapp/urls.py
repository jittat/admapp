"""admapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from django.contrib.auth import views as auth_views

import main.views

urlpatterns = [
    url(r'^$', main.views.index, name='main-index'),
    url(r'^regis/', include('regis.urls')),
    url(r'^appl/', include('appl.urls')),
    url(r'^backoffice/', include('backoffice.urls')),
    url(r'^admin/', admin.site.urls),


    url(r'^accounts/login/$',
        auth_views.LoginView.as_view(template_name='backoffice/accounts/login.html'),
        name='backoffice-login'),
    url(r'^accounts/logout/$',
        auth_views.LogoutView.as_view(),
        name='backoffice-logout'),
]

