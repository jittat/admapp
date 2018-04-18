from django.conf.urls import url, include

from appl import views
from appl.views import upload as upload_views
from appl.views import general_forms
from appl.views import major_selection
from appl.views import print_views

app_name = 'appl'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^round/(?P<admission_round_id>\d+)$', views.index, name='index-with-round'),

    url(r'^personal/$', general_forms.personal_profile, name='personal-profile'),

    url(r'^education/$', general_forms.education_profile, name='education-profile'),
    url(r'^school_search/$', general_forms.ajax_school_search, name='ajax-school-search'),
    url(r'^topschool_list/$', general_forms.ajax_topschool_list, name='ajax-topschool-list'),

    url(r'^apply/(\d+)/(\d+)/$', views.apply_project, name='apply-project'),
    url(r'^cancel/(\d+)/(\d+)/$', views.cancel_project, name='cancel-project'),

    url(r'^cancelsp/(\d+)/(\d+)/$', views.cancel_project_special, name='cancel-project-special'),

    url(r'^select/(\d+)/$', major_selection.select, name='major-selection'),

    url(r'^payment/(\d+)/$', views.payment, name='payment'),
    url(r'^payment/(\d+)/barcode/(\d+)\.png$', views.payment_barcode, name='payment-barcode'),
    
    url(r'^upload/(\d+)/$', upload_views.upload, name='upload'),
    url(r'^doc/(?P<applicant_id>\d+)/(?P<project_uploaded_document_id>\d+)/(?P<document_id>\d+)/$', upload_views.document_download, name='document-download'),
    url(r'^doc/(?P<applicant_id>\d+)/(?P<project_uploaded_document_id>\d+)/(?P<document_id>\d+)/delete/$', upload_views.document_delete, name='document-delete'),

    url(r'^status/$', views.check_application_documents, name='check-project-documents'),

    url(r'^natsport/print/$', print_views.sport_print, name='natsport-print'),
    url(r'^ap/print/$', print_views.ap_print, name='ap-print'),
    url(r'^el/print/$', print_views.el_print, name='el-print'),
    url(r'^gensport/print/$', print_views.gen_sport_print, name='gensport-print'),
    url(r'^kus/print/$', print_views.kus_print, name='kus-print'),
    url(r'^culture/print/$', print_views.culture_print, name='culture-print'),
    url(r'^inter/print/$', print_views.inter_print, name='inter-print'),

    url(r'^common/print/$', print_views.common_print, name='common-print'),
]
