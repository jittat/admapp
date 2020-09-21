from django.conf.urls import url, include
from django.urls import path

from . import views
from backoffice.views import payments
from backoffice.views import projects
from backoffice.views import users
from backoffice.views import reports
from backoffice.views import adjustment
from backoffice.views import criterion

app_name = 'backoffice'

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^payment/$', payments.index, name='payment-index'),
    url(r'^payment/update/(?P<payment_id>\d+)/$',
        payments.update, name='payment-update'),

    url(r'^applicants/([0-9a-zA-Z\d]\d+)/$',
        views.show, name='show-applicant'),
    url(r'^applicants/(\d+)/([0-9a-zA-Z]\d*)/$',
        views.show, name='show-applicant-in-project'),

    url(r'^new_password/([0-9a-zA-Z]\d+)/$',
        views.new_password, name='new-password'),
    url(r'^update/([0-9a-zA-Z]\d+)/$',
        views.update_applicant, name='update-applicant'),

    url(r'^login/(\d+)/(.+)/$', views.login_as_applicant, name='login-as-applicant'),

    url(r'^search/$', views.search, name='search'),
    url(r'^search/(\d+)/$', views.search, name='search-project'),

    url(r'^projects/(\d+)/(\d+)/$', projects.index, name='projects-index'),
    url(r'^projects/(\d+)/(\d+)/list/$',
        projects.list_applicants, name='projects-list'),
    url(r'^projects/(\d+)/(\d+)/majors/$',
        projects.list_major_details, name='projects-list-majors'),
    url(r'^projects/(\d+)/(\d+)/interview-descriptions/$', projects.list_major_interview_descriptions,
        name='projects-list-majors-interview-descriptions'),

    url(r'^projects/applicants/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/(?P<rank>\d+)/$',
        projects.show_applicant, name='projects-show-applicant'),

    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/doc/(\d+)/(\d+)/(\d+)/$',
        projects.download_applicant_document,
        name='projects-download-app-document'),

    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/marks/(\d+)/$',
        projects.check_mark_toggle,
        name='projects-check-mark-toggle'),

    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/comments/$',
        projects.save_comment,
        name='projects-save-comment'),
    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/comment/(\d+)/delete/$',
        projects.delete_comment,
        name='projects-delete-comment'),

    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/criteria/(.+)/$',
        projects.set_criteria_result,
        name='projects-set-criteria-result'),
    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/interview/(.+)/$',
        projects.set_call_for_interview,
        name='projects-set-call-for-interview'),
    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/acceptance/(.+)/$',
        projects.set_acceptance,
        name='projects-set-acceptance'),

    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/sheet$',
        reports.download_applicants_sheet,
        name='projects-download-app-sheet'),

    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/sheet/interview$',
        reports.download_applicants_sheet,
        {'only_interview': True},
        name='projects-download-app-sheet-only-interview'),

    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/interview-sheet$',
        reports.download_applicants_interview_sheet,
        name='projects-download-app-interview-sheet'),

    url(r'^projects/applicants/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/interview-score-sheet$',
        reports.download_applicants_interview_score_sheet,
        name='projects-download-app-interview-score-sheet'),

    url(r'^projects/scores/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/$',
        projects.show_scores, name='projects-show-scores'),
    url(r'^projects/scores/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/interview_score/$',
        projects.update_interview_call_score, name='projects-interview-call-score-update'),

    url(r'^projects/calls/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/$',
        projects.list_applicants_for_acceptance_calls, name='projects-list-applicants-for-acceptance-calls'),
    url(r'^projects/calls/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/update/$',
        projects.update_applicant_acceptance_call, name='projects-update-applicant-acceptance-call'),

    url(r'^users/$', users.index, name='users-index'),

    url(r'^adjustment/$',
        adjustment.index,
        name='adjustment'),
    path('adjustment/<major_full_code>/',
         adjustment.major_index,
         name='adjustment-major'),
    url(r'^criteria/', include('criteria.urls')),
]
