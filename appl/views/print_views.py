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
    1: '013',
    2: '012',
    3: '014',
    4: '015',
    5: '011',
    6: '031',
    7: '051',
    8: '061',
    9: '070',
    10: '081',
    11: '082',
    12: '091',
    13: '092',
    14: '093',
    15: '094',
    16: '103',
    17: '101',
    18: '102',
    19: '102',
    20: '104',
    21: '110',
    22: '130',
    23: '041',
    24: '042',
    25: '021',
    26: '022',
    27: '023',
    28: '024',
    29: '141',
    30: '142',
    31: '121',
    32: '122',
    33: '123',
    34: '151',
    35: '171',
    36: '181',
    37: '182',
    38: '191',
    39: '192',
    40: '193',
    41: '194',
    42: '161',
    43: '162',
    44: '163',
    45: '201',
    46: '202',
    47: '241',
    48: '252',
    49: '251',
    50: '212',
    51: '213',
    52: '214',
    53: '215',
    54: '217',
    55: '216',
    56: '211',
    57: '223',
    58: '221',
    59: '222',
    60: '234',
    61: '231',
    62: '233',
    63: '236',
    64: '232',
    65: '235',
    66: '262',
    67: '261',
    68: '265',
    69: '264',
    70: '263',
    71: '276',
    72: '275',
    73: '271',
    74: '272',
    75: '273',
    76: '274',
    77: '281',
    78: '282',
    79: '283',
    80: '284',
    81: '285',
    82: '286',
    83: '288',
    84: '287',
}

@appl_login_required
def sport_print(request):
    applicant = request.applicant
    admission_round = AdmissionRound.get_available()
    
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
    admission_round = AdmissionRound.get_available()
    
    personal_profile = applicant.get_personal_profile()
    educational_profile = applicant.get_educational_profile()

    active_application = applicant.get_active_application(admission_round)

    admission_project = active_application.admission_project
    if admission_project.id != 4:
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
    admission_round = AdmissionRound.get_available()
    
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
    admission_round = AdmissionRound.get_available()
    
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
    admission_round = AdmissionRound.get_available()
    
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






