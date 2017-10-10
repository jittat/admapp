from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, HttpResponse

from regis.models import Applicant, LogItem
from regis.decorators import appl_login_required

from appl.models import AdmissionProject, ProjectUploadedDocument, AdmissionRound, Payment, ProjectApplication, AdmissionProjectRound, Eligibility

from appl.views import load_supplements

@appl_login_required
def sport_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.get_available()
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)
    admission_project = active_application.admission_project

    major_selection = active_application.get_major_selection()

    supplement_configs = load_supplements(applicant,
                                          admission_project)

    sport_type = supplement_configs[0].supplement_instance.get_data()
    sport_history = supplement_configs[1].supplement_instance.get_data()

    return render(request,
                  'appl/print/natsport_print.html',
                  { 'applicant': applicant,
                    'personal_profile': personal_profile,
                    'educational_profile': educational_profile,
                    'majors': major_selection.get_majors(),

                    'sport_type': sport_type,
                    'sport_history': sport_history, })
