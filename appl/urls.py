from django.urls import re_path

from appl import views
from appl.views import general_forms
from appl.views import major_selection
from appl.views import print_views
from appl.views import upload as upload_views

app_name = 'appl'
urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^round/(?P<admission_round_id>\d+)$', views.index, name='index-with-round'),

    re_path(r'^personal/$', general_forms.personal_profile, name='personal-profile'),

    re_path(r'^education/$', general_forms.education_profile, name='education-profile'),
    re_path(r'^school_search/$', general_forms.ajax_school_search, name='ajax-school-search'),
    re_path(r'^topschool_list/$', general_forms.ajax_topschool_list, name='ajax-topschool-list'),

    re_path(r'^apply/(\d+)/(\d+)/$', views.apply_project, name='apply-project'),
    re_path(r'^cancel/(\d+)/(\d+)/$', views.cancel_project, name='cancel-project'),

    re_path(r'^cancelsp/(\d+)/(\d+)/$', views.cancel_project_special, name='cancel-project-special'),

    re_path(r'^select/(\d+)/$', major_selection.select, name='major-selection'),

    re_path(r'^payment/(\d+)/$', views.payment, name='payment'),
    re_path(r'^payment/(\d+)/qr/$', views.payment_with_qr_code, name='payment-qr'),
    re_path(r'^payment/(\d+)/barcode/(\d+)\.png$', views.payment_barcode, name='payment-barcode'),
    re_path(r'^payment/(\d+)/qrcode/(\d+)\.png$', views.payment_qrcode, name='payment-qrcode'),

    re_path(r'^payment/fee-amount/$', views.get_additional_payment, name='payment-fee-amount'),
    
    re_path(r'^upload/(\d+)/$', upload_views.upload, name='upload'),
    re_path(r'^doc/(?P<applicant_id>\d+)/(?P<project_uploaded_document_id>\d+)/(?P<document_id>\d+)/$', upload_views.document_download, name='document-download'),
    re_path(r'^doc/(?P<applicant_id>\d+)/(?P<project_uploaded_document_id>\d+)/(?P<document_id>\d+)/delete/$', upload_views.document_delete, name='document-delete'),

    re_path(r'^status/$', views.check_application_documents, name='check-project-documents'),

    re_path(r'^natsport/print/$', print_views.sport_print, name='natsport-print'),
    re_path(r'^ap/print/$', print_views.ap_print, name='ap-print'),
    re_path(r'^el/print/$', print_views.el_print, name='el-print'),
    re_path(r'^gensport/print/$', print_views.gen_sport_print, name='gensport-print'),
    re_path(r'^kus/print/$', print_views.kus_print, name='kus-print'),
    re_path(r'^culture/print/$', print_views.culture_print, name='culture-print'),
    re_path(r'^inter/print/$', print_views.inter_print, name='inter-print'),

    re_path(r'^common/print/$', print_views.common_print, name='common-print'),
]
