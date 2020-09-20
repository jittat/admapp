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
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from django.contrib.auth import views as auth_views

import main.views

urlpatterns = i18n_patterns(
    url(r'^$', main.views.index, name='main-index'),
    url(r'^regis/', include('regis.urls')),
    url(r'^appl/', include('appl.urls')),
    url(r'^supp/', include('supplements.urls')),
    url(r'^backoffice/', include('backoffice.urls')),
    url(r'^qr/', include('qrconfirmations.urls')),

    url(r'^api/', include('api.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),

    url(r'^accounts/login/$',
        auth_views.LoginView.as_view(
            template_name='backoffice/accounts/login.html'),
        name='backoffice-login'),
    url(r'^accounts/logout/$',
        auth_views.LogoutView.as_view(),
        name='backoffice-logout'),

    prefix_default_language=False
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
