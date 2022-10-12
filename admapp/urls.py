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
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import re_path, include

import main.views

urlpatterns = i18n_patterns(
    re_path(r'^$', main.views.index, name='main-index'),
    re_path(r'^regis/', include('regis.urls')),
    re_path(r'^appl/', include('appl.urls')),
    re_path(r'^supp/', include('supplements.urls')),
    re_path(r'^backoffice/', include('backoffice.urls')),
    re_path(r'^qr/', include('qrconfirmations.urls')),
    
    re_path(r'^api/', include('api.urls')),
    
    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^admin/', admin.site.urls),
    
    re_path(r'^accounts/login/$',
            auth_views.LoginView.as_view(
                template_name='backoffice/accounts/login.html'),
            name='backoffice-login'),
    re_path(r'^accounts/logout/$',
            auth_views.LogoutView.as_view(),
            name='backoffice-logout'),

    prefix_default_language=False
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
