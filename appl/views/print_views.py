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
    9: 1404,
    10: 1501,
    11: 1502,
    12: 1503,
    13: 1504,
    14: 1505,
    15: 1506,
    16: 1507,
    17: 1508,
    18: 1509,
    19: 1510,
    20: 1511,
    21: 1601,
    22: 1602,
    23: 1701,
    24: 1702,
    25: 1801,
    26: 1802,
    27: 1803,
    28: 1804,
    29: 1805,
    30: 1806,
    31: 1807,
    32: 1808,
    33: 1809,
    34: 1810,
    35: 1811,
    36: 1901,
    37: 2001,
    38: 2002,
    39: 2101,
    40: 2201,
    41: 2202,
    42: 2203,
    43: 2204,
    44: 2301,
    45: 2302,
    46: 2303,
    47: 2401,
    48: 2402,
    49: 2501,
    50: 2601,
    51: 2602,
    52: 2701,
    53: 2702,
    54: 2703,
    55: 2704,
    56: 2705,
    57: 2706,
    58: 2707,
    59: 2708,
    60: 2709,
    61: 2710,
    62: 2711,
    63: 2712,
    64: 2713,
    65: 2714,
    66: 2715,
    67: 2801,
    68: 2802,
    69: 2803,
    70: 2901,
    71: 2902,
    72: 2903,
    73: 3001,
    74: 3101,
    75: 3102,
    76: 3103,
    77: 3104,
    78: 3201,
    79: 3202,
    80: 3203,
    81: 3204,
    82: 3205,
    83: 3301,
    84: 3302,
    85: 3303,
    86: 3304,
    87: 3305,
    88: 3401,
    89: 3402,
    90: 3403,
    91: 3404,
    92: 3405,
    93: 3406,
    94: 3407,
    95: 3408,
    96: 3409,
    97: 3501,
    98: 3502,
    99: 3503,
    100: 3504,
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






