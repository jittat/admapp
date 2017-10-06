from django.conf.urls import url, include

from appl import views
from appl.views import upload as upload_views
from appl.views import general_forms
from appl.views import major_selection

app_name = 'appl'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^upload/(\d+)/$', upload_views.upload, name='upload'),

    url(r'^personal/$', general_forms.personal_profile, name='personal-profile'),
    url(r'^education/$', general_forms.education_profile, name='education-profile'),
    url(r'^school_search/$', general_forms.ajax_school_search, name='ajax-school-search'),

    url(r'^apply/(\d+)/(\d+)/$', views.apply_project, name='apply-project'),

    url(r'^select/(\d+)/$', major_selection.select, name='major-selection'),

    url(r'^payment/(\d+)/$', views.payment, name='payment'),
    url(r'^payment/(\d+)/barcode/(\d+)\.png$', views.payment_barcode, name='payment-barcode'),
    url(r'^doc/(?P<applicant_id>\d+)/(?P<admission_project_id>\d+)/(?P<document_id>\d+)/$', upload_views.document_download, name='document-download'),
    url(r'^doc/(?P<applicant_id>\d+)/(?P<admission_project_id>\d+)/(?P<document_id>\d+)/delete/$', upload_views.document_delete, name='document-delete'),
]
