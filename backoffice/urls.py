from django.conf.urls import url, include

from . import views
from backoffice.views import payments
from backoffice.views import projects
from backoffice.views import users
from backoffice.views import reports

app_name = 'backoffice'

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^payment/$', payments.index, name='payment-index'),
    url(r'^payment/update/(?P<payment_id>\d+)/$', payments.update, name='payment-update'),

    url(r'^applicants/(\d+)/$', views.show, name='show-applicant'),
    url(r'^applicants/(\d+)/(\d+)/$', views.show, name='show-applicant-in-project'),

    url(r'^new_password/(\d+)/$', views.new_password, name='new-password'),
    url(r'^update/(\d+)/$', views.update_applicant, name='update-applicant'),

    url(r'^login/(\d+)/(.+)/$', views.login_as_applicant, name='login-as-applicant'),

    url(r'^search/$', views.search, name='search'),
    url(r'^search/(\d+)/$', views.search, name='search-project'),

    url(r'^projects/(\d+)/(\d+)/$', projects.index, name='projects-index'),
    url(r'^projects/(\d+)/(\d+)/list/$', projects.list_applicants, name='projects-list'),

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

    url(r'^projects/applicants/(\d+)/(\d+)/(\d+)/interview-sheet$',
        reports.download_applicants_interview_sheet,
        name='projects-download-app-interview-sheet'),

    url(r'^projects/scores/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/$',
        projects.show_scores, name='projects-show-scores'),
    url(r'^projects/scores/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/interview_score/$',
        projects.update_interview_call_score, name='projects-interview-call-score-update'),

    url(r'^users/$', users.index, name='users-index'),
]
