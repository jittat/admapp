from django.urls import path
from django.urls import re_path, include

from backoffice.views import adjustment
from backoffice.views import payments
from backoffice.views import projectoptions
from backoffice.views import projects
from backoffice.views import reports
from backoffice.views import users
from backoffice.views import interviews
from . import views

app_name = "backoffice"

urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^payment/$", payments.index, name="payment-index"),
    re_path(r"^payment/update/(?P<payment_id>\d+)/$", payments.update, name="payment-update"),
    re_path(r"^applicants/([0-9a-zA-Z\d]\d+)/$", views.show, name="show-applicant"),
    re_path(r"^applicants/(\d+)/([0-9a-zA-Z]\d*)/$", views.show, name="show-applicant-in-project"),
    re_path(r"^new_password/([0-9a-zA-Z]\d+)/$", views.new_password, name="new-password"),
    re_path(r"^update/([0-9a-zA-Z]\d+)/$", views.update_applicant, name="update-applicant"),
    re_path(r"^login/(\d+)/(.+)/$", views.login_as_applicant, name="login-as-applicant"),
    re_path(r"^search/$", views.search, name="search"),
    re_path(r"^search/(\d+)/$", views.search, name="search-project"),
    re_path(
        r"^appinfo/$",
        projectoptions.show_project_application_info,
        name="show_project_application_info",
    ),
    re_path(r"^options/$", projectoptions.show_project_options, name="show_project_options"),
    re_path(
        r"^options/(\d+)/(.+)/(\d+)/$",
        projectoptions.update_project_options,
        name="update_project_options",
    ),
    re_path(r"^projects/(\d+)/(\d+)/$", projects.index, name="projects-index"),
    re_path(r"^projects/(\d+)/(\d+)/list/$", projects.list_applicants, name="projects-list"),
    re_path(
        r"^projects/(\d+)/(\d+)/majors/$", projects.list_major_details, name="projects-list-majors"
    ),
    re_path(
        r"^projects/(\d+)/(\d+)/interview-descriptions/$",
        projects.list_major_interview_descriptions,
        name="projects-list-majors-interview-descriptions",
    ),
    re_path(
        r"^projects/applicants/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/(?P<rank>\d+)/$",
        projects.show_applicant,
        name="projects-show-applicant",
    ),
    re_path(
        r"^projects/applicants/(\d+)/(\d+)/(\d+)/doc/(\d+)/(\d+)/(\d+)/$",
        projects.download_applicant_document,
        name="projects-download-app-document",
    ),
    re_path(
        r"^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/marks/(\d+)/$",
        projects.check_mark_toggle,
        name="projects-check-mark-toggle",
    ),
    re_path(
        r"^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/comments/$",
        projects.save_comment,
        name="projects-save-comment",
    ),
    re_path(
        r"^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/comment/(\d+)/delete/$",
        projects.delete_comment,
        name="projects-delete-comment",
    ),
    re_path(
        r"^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/criteria/(.+)/$",
        projects.set_criteria_result,
        name="projects-set-criteria-result",
    ),
    re_path(
        r"^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/interview/(.+)/$",
        projects.set_call_for_interview,
        name="projects-set-call-for-interview",
    ),
    re_path(
        r"^projects/applicants/(\d+)/(\d+)/(\d+)/(\d+)/acceptance/(.+)/$",
        projects.set_acceptance,
        name="projects-set-acceptance",
    ),
    re_path(
        r"^projects/applicants/(\d+)/(\d+)/(\d+)/sheet$",
        reports.download_applicants_sheet,
        name="projects-download-app-sheet",
    ),
    re_path(
        r"^projects/applicants/(\d+)/(\d+)/(\d+)/sheet/interview$",
        reports.download_applicants_sheet,
        {"only_interview": True},
        name="projects-download-app-sheet-only-interview",
    ),
    re_path(
        r"^projects/applicants/(\d+)/(\d+)/(\d+)/interview-sheet$",
        reports.download_applicants_interview_sheet,
        name="projects-download-app-interview-sheet",
    ),
    re_path(
        r"^projects/applicants/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/score-sheet$",
        reports.download_applicants_score_sheet,
        name="projects-download-app-score-sheet",
    ),
    re_path(
        r"^projects/applicants/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/interview-score-sheet$",
        reports.download_applicants_interview_score_sheet,
        name="projects-download-app-interview-score-sheet",
    ),
    re_path(
        r"^projects/scores/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/$",
        projects.show_scores,
        name="projects-show-scores",
    ),
    re_path(
        r"^projects/scores/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/interview_score/$",
        projects.update_interview_call_score,
        name="projects-interview-call-score-update",
    ),
    re_path(
        r"^projects/calls/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/$",
        projects.list_applicants_for_acceptance_calls,
        name="projects-list-applicants-for-acceptance-calls",
    ),
    re_path(
        r"^projects/calls/(?P<project_id>\d+)/(?P<round_id>\d+)/(?P<major_number>\d+)/update/$",
        projects.update_applicant_acceptance_call,
        name="projects-update-applicant-acceptance-call",
    ),
    re_path(r"^users/$", users.index, name="users-index"),
    re_path(r"^adjustment/$", adjustment.index, name="adjustment"),
    path("adjustment/report/<round_number>/", adjustment.adjustment_list, name="adjustment-report"),
    path("adjustment/<major_full_code>/", adjustment.major_index, name="adjustment-major"),
    re_path(r"^criteria/", include("criteria.urls")),
    path(
        "interviews/delete/<int:description_id>/",
        interviews.delete,
        name="interviews-delete",
    ),
    path(
        "interviews/<int:description_id>/",
        interviews.interview,
        name="interviews-view",
        ),
    path(
        "interviews/<admission_round_id>/<faculty_id>/",
        interviews.interview_form,
        {"description_id": None},
        name="interviews-create",
    ),
    path(
        "interviews/<admission_round_id>/<faculty_id>/<int:description_id>/",
        interviews.interview_form,
        name="interviews-edit",
    ),
    path(
        "interviews-image/<int:description_id>/<str:type>",
        interviews.interview_image,
        name="interviews-image",
    ),
    path(
        "interviews-list/<admission_round_id>/<faculty_id>/",
        interviews.list_interview_forms,
        {"description_id": None},
        name="interviews-list",
    ),
]
