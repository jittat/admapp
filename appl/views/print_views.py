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
    19: 1511,
    20: 1601,
    21: 1602,
    22: 1701,
    23: 1702,
    24: 1801,
    25: 1802,
    26: 1803,
    27: 1804,
    28: 1805,
    29: 1806,
    30: 1807,
    31: 1808,
    32: 1809,
    33: 1810,
    34: 1811,
    35: 1901,
    36: 2001,
    37: 2002,
    38: 2101,
    39: 2201,
    40: 2202,
    41: 2203,
    42: 2204,
    43: 2301,
    44: 2302,
    45: 2303,
    46: 2401,
    47: 2402,
    48: 2501,
    49: 2601,
    50: 2602,
    51: 2701,
    52: 2702,
    53: 2703,
    54: 2704,
    55: 2705,
    56: 2706,
    57: 2707,
    58: 2708,
    59: 2709,
    60: 2710,
    61: 2711,
    62: 2712,
    63: 2713,
    64: 2714,
    65: 2715,
    66: 2801,
    67: 2901,
    68: 2902,
    69: 2903,
    70: 3001,
    71: 3101,
    72: 3102,
    73: 3103,
    74: 3104,
    75: 3201,
    76: 3202,
    77: 3203,
    78: 3204,
    79: 3205,
    80: 3206,
    81: 3301,
    82: 3302,
    83: 3303,
    84: 3304,
    85: 3305,
    86: 3306,
    87: 3401,
    88: 3402,
    89: 3403,
    90: 3404,
    91: 3405,
    92: 3406,
    93: 3407,
    94: 3408,
    95: 3409,
    96: 3501,
    97: 3502,
    98: 3503,
    99: 3504,
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






