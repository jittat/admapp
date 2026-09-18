from django.http import HttpResponseForbidden
from django.shortcuts import render

from appl.models import AdmissionResult
from appl.models import AdmissionRound
from regis.decorators import appl_login_required
from supplements.models import load_supplement_configs_with_instance
from supplements.views.blocks import load_ap_course_results

SPORT_MAJOR_NUMBER_MAP = {
    1: 1001,
    2: 1101,
    3: 1102,
    4: 1201,
    5: 1301,
    6: 1401,
    7: 1402,
    8: 1403,
    9: 1501,
    10: 1502,
    11: 1503,
    12: 1504,
    13: 1505,
    14: 1506,
    15: 1507,
    16: 1508,
    17: 1509,
    18: 1510,
    19: 1601,
    20: 1602,
    21: 1701,
    22: 1801,
    23: 1802,
    24: 1803,
    25: 1804,
    26: 1805,
    27: 1806,
    28: 1807,
    29: 1808,
    30: 1809,
    31: 1901,
    32: 1902,
    33: 2001,
    34: 2101,
    35: 2102,
    36: 2103,
    37: 2104,
    38: 2201,
    39: 2202,
    40: 2203,
    41: 2301,
    42: 2302,
    43: 2401,
    44: 2501,
    45: 2502,
    46: 2601,
    47: 2602,
    48: 2603,
    49: 2604,
    50: 2605,
    51: 2606,
    52: 2607,
    53: 2608,
    54: 2609,
    55: 2610,
    56: 2611,
    57: 2701,
    58: 2702,
    59: 2703,
    60: 2801,
    61: 2901,
    62: 2902,
    63: 3001,
    64: 3002,
    65: 3003,
    66: 3004,
    67: 3005,
    68: 3006,
    69: 3101,
    70: 3102,
    71: 3103,
    72: 3104,
    73: 3105,
    74: 3106,
    75: 3201,
    76: 3202,
    77: 3203,
    78: 3204,
    79: 3205,
    80: 3206,
    81: 3207,
    82: 3208,
    83: 3301,
    84: 3302,
    85: 3303,
    86: 3304,
}

@appl_login_required
def sport_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.objects.get(pk=1)
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)

    if not active_application:
        return HttpResponseForbidden()
    
    admission_project = active_application.admission_project
    if admission_project.id != 4:
        return HttpResponseForbidden()

    major_selection = active_application.get_major_selection()
    majors = major_selection.get_majors()
    for m in majors:
        if m.number in SPORT_MAJOR_NUMBER_MAP:
            m.display_number = str(SPORT_MAJOR_NUMBER_MAP[m.number])
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
    admission_round = AdmissionRound.objects.get(pk=1)
    
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






