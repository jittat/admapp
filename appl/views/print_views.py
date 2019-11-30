from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, HttpResponse

from regis.models import Applicant, LogItem
from regis.decorators import appl_login_required

from appl.models import AdmissionProject, AdmissionRound, AdmissionProjectRound
from appl.models import Payment, ProjectApplication
from appl.models import AdmissionResult

from supplements.models import load_supplement_configs_with_instance
from supplements.views.blocks import load_ap_course_results

SPORT_MAJOR_NUMBER_MAP = {
}

@appl_login_required
def sport_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.objects.get(pk=1)
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)
    admission_project = active_application.admission_project

    major_selection = active_application.get_major_selection()
    majors = major_selection.get_majors()
    for m in majors:
        if m.number in SPORT_MAJOR_NUMBER_MAP:
            m.display_number = SPORT_MAJOR_NUMBER_MAP[m.number]
        else:
            m.display_number = str(m.number)

    supplement_configs = load_supplement_configs_with_instance(applicant,
                                                               admission_project)

    sport_type = supplement_configs[0].supplement_instance.get_data()
    sport_history = supplement_configs[1].supplement_instance.get_data()

    return render(request,
                  'appl/print/natsport_print.html',
                  { 'applicant': applicant,
                    'personal_profile': personal_profile,
                    'educational_profile': educational_profile,
                    'majors': majors,

                    'sport_type': sport_type,
                    'sport_history': sport_history, })


@appl_login_required
def ap_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.objects.get(pk=1)
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)

    admission_project = active_application.admission_project
    if admission_project.id != 2:
        return HttpResponseForbidden()

    project_round = admission_project.get_project_round_for(admission_round)
    if not project_round.accepted_for_interview_result_shown:
        return HttpResponseForbidden()
    
    major_selection = active_application.get_major_selection()
    majors = major_selection.get_majors()

    admission_results = AdmissionResult.find_by_application(active_application)
    is_accepted_for_interview = False
    for res in admission_results:
        if res.is_accepted_for_interview:
            is_accepted_for_interview = True

    if not is_accepted_for_interview:
        return HttpResponseForbidden()

    ap_courses = load_ap_course_results(applicant, admission_project, admission_round)
            
    mresults = dict([(res.major_id, res) for res in admission_results])
    for major in majors:
        if major.id not in mresults:
            major.is_accepted_for_interview = False
        else:
            major.is_accepted_for_interview = mresults[major.id].is_accepted_for_interview
    
    return render(request,
                  'appl/print/ap_print.html',
                  { 'applicant': applicant,
                    'personal_profile': personal_profile,
                    'educational_profile': educational_profile,
                    'majors': majors,
                    'ap_courses': ap_courses, })


@appl_login_required
def el_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.objects.get(pk=1)
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)

    admission_project = active_application.admission_project
    if admission_project.id != 1:
        return HttpResponseForbidden()

    project_round = admission_project.get_project_round_for(admission_round)
    if not project_round.accepted_for_interview_result_shown:
        return HttpResponseForbidden()
    
    major_selection = active_application.get_major_selection()
    majors = major_selection.get_majors()

    admission_results = AdmissionResult.find_by_application(active_application)
    is_accepted_for_interview = False
    for res in admission_results:
        if res.is_accepted_for_interview:
            is_accepted_for_interview = True

    if not is_accepted_for_interview:
        return HttpResponseForbidden()

    mresults = dict([(res.major_id, res) for res in admission_results])
    for major in majors:
        if major.id not in mresults:
            major.is_accepted_for_interview = False
        else:
            major.is_accepted_for_interview = mresults[major.id].is_accepted_for_interview
    
    return render(request,
                  'appl/print/el_print.html',
                  { 'applicant': applicant,
                    'personal_profile': personal_profile,
                    'educational_profile': educational_profile,
                    'majors': majors })


@appl_login_required
def gen_sport_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.objects.get(pk=2)
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)
    admission_project = active_application.admission_project

    major_selection = active_application.get_major_selection()
    majors = major_selection.get_majors()
    supplement_configs = load_supplement_configs_with_instance(applicant,
                                                               admission_project)

    sport_type = supplement_configs[0].supplement_instance.get_data()

    try:
        from supplements.views.forms.gen_sport import GEN_SPORT_LEVEL_CHOICES
        sport_level = dict(GEN_SPORT_LEVEL_CHOICES)[str(sport_type['gen_sport_level'])]
    except:
        sport_level = ''
        
    sport_history = supplement_configs[1].supplement_instance.get_data()

    return render(request,
                  'appl/print/gensport_print.html',
                  { 'applicant': applicant,
                    'personal_profile': personal_profile,
                    'educational_profile': educational_profile,
                    'majors': majors,

                    'sport_type': sport_type,
                    'sport_level': sport_level,
                    'sport_history': sport_history, })


@appl_login_required
def kus_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.objects.get(pk=2)
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)
    admission_project = active_application.admission_project

    major_selection = active_application.get_major_selection()
    majors = major_selection.get_majors()

    return render(request,
                  'appl/print/kus_print.html',
                  { 'applicant': applicant,
                    'personal_profile': personal_profile,
                    'educational_profile': educational_profile,
                    'majors': majors, })


@appl_login_required
def culture_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.objects.get(pk=3)
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)
    admission_project = active_application.admission_project

    major_selection = active_application.get_major_selection()
    majors = major_selection.get_majors()
    supplement_configs = load_supplement_configs_with_instance(applicant,
                                                               admission_project)

    cultural_type = supplement_configs[0].supplement_instance.get_data()
    cultural_history = supplement_configs[1].supplement_instance.get_data()
    cultural_exam = supplement_configs[2].supplement_instance.get_data()

    return render(request,
                  'appl/print/culture_print.html',
                  { 'applicant': applicant,
                    'personal_profile': personal_profile,
                    'educational_profile': educational_profile,
                    'majors': majors,

                    'cultural_type': cultural_type,
                    'cultural_exam': cultural_exam,
                    'cultural_history': cultural_history, })


@appl_login_required
def inter_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.objects.get(pk=1)
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)

    admission_project = active_application.admission_project
    if admission_project.id != 3:
        return HttpResponseForbidden()

    project_round = admission_project.get_project_round_for(admission_round)
    if not project_round.accepted_for_interview_result_shown:
        return HttpResponseForbidden()
    
    major_selection = active_application.get_major_selection()
    majors = major_selection.get_majors()

    admission_results = AdmissionResult.find_by_application(active_application)
    is_accepted_for_interview = False
    for res in admission_results:
        if res.is_accepted_for_interview:
            is_accepted_for_interview = True

    if not is_accepted_for_interview:
        return HttpResponseForbidden()

    mresults = dict([(res.major_id, res) for res in admission_results])
    for major in majors:
        if major.id not in mresults:
            major.is_accepted_for_interview = False
        else:
            major.is_accepted_for_interview = mresults[major.id].is_accepted_for_interview
    
    return render(request,
                  'appl/print/inter_print.html',
                  { 'applicant': applicant,
                    'personal_profile': personal_profile,
                    'educational_profile': educational_profile,
                    'majors': majors })

@appl_login_required
def common_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.objects.get(pk=2)
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)
    if not active_application:
        return HttpResponseForbidden()

    admission_project = active_application.admission_project
    #if admission_project.id not in [28,36]:
    #    return HttpResponseForbidden()

    project_round = admission_project.get_project_round_for(admission_round)
    if not project_round.accepted_for_interview_result_shown:
        return HttpResponseForbidden()
    
    major_selection = active_application.get_major_selection()
    majors = major_selection.get_majors()

    admission_results = AdmissionResult.find_by_application(active_application)
    is_accepted_for_interview = False
    for res in admission_results:
        if res.is_accepted_for_interview:
            is_accepted_for_interview = True

    if not is_accepted_for_interview:
        return HttpResponseForbidden()

    mresults = dict([(res.major_id, res) for res in admission_results])
    for major in majors:
        if major.id not in mresults:
            major.is_accepted_for_interview = False
        else:
            major.is_accepted_for_interview = mresults[major.id].is_accepted_for_interview
    
    return render(request,
                  'appl/print/common_print.html',
                  { 'applicant': applicant,
                    'application_number': active_application.get_number(),
                    'admission_project': admission_project,
                    'personal_profile': personal_profile,
                    'educational_profile': educational_profile,
                    'majors': majors })






