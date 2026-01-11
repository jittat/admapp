import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import Http404, HttpResponse
from django.contrib import messages

from backoffice.models import APIToken
from appl.models import AdmissionProject, AdmissionRound, Major
from appl.models import Applicant, ProjectApplication, AdmissionResult, MajorSelection, PersonalProfile

def valid_token_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        token_auth = request.META.get("HTTP_AUTHORIZATION")
        items = token_auth.split(" ") if token_auth else []
        if len(items) == 2 and (items[0] == 'Bearer' or items[0] == 'Token'):
            token = items[1]
        else:
            token = None
        if not token or not APIToken.objects.filter(token=token).exists():
            return HttpResponse(status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@valid_token_required
def projects(request):
    projects = AdmissionProject.objects.filter(is_visible_in_backoffice=True).all()
    return HttpResponse(json.dumps({"projects": [{
        'id':p.id, 
        'title': p.title,
        'cupt_code': p.cupt_code,
    } for p in projects]}), 
    content_type="application/json")


def get_admission_result(application,
                         admission_project,
                         admission_round,
                         major):
    results = AdmissionResult.objects.filter(application=application,
                                             admission_project=admission_project,
                                             admission_round=admission_round,
                                             major=major).all()
    if len(results) == 0:
        return None
    else:
        return results[0]

def extract_raw_data(applicant, application, personal_profile, app_date, cupt_major,
                   app_type, tcas_id, ranking, applicant_status, interview_description,
                   header):
    university_id = '002'

    data = {
        'university_id': university_id,
        'program_id': cupt_major['program_id'],
        'major_id': cupt_major['major_id'],
        'project_id': cupt_major['project_id'],
        'type': app_type,
        'citizen_id': '',
        #'gnumber': '',
        #'passport': '',
        'title': applicant.prefix,
        'first_name_th': applicant.first_name,
        'last_name_th': applicant.last_name,
        'first_name_en': personal_profile.first_name_english,
        'last_name_en': personal_profile.last_name_english,
        'priority': 0,
        #'application_id': application.get_number(),
        #'application_date': app_date,
        #'tcas_id': tcas_id,
        'ranking': ranking,
        'score': 0,
        #'interview_status': interview_status,
        #'interview_description': interview_description,
        #'status': 0,
        'tcas_status': 0,
        'applicant_status': applicant_status,
        'interview_reason': '0',
    }

    if not applicant.has_registered_with_passport():
        data['citizen_id'] = applicant.national_id
    else:
        data['citizen_id'] = applicant.passport_number

    return { h:data[h] for h in header }

APPLICANT_FIELDS = [
    'university_id',
    'program_id',
    'major_id',
    'project_id',
    'type',
    'citizen_id',
    'title',
    'first_name_th',
    'last_name_th',
    'first_name_en',
    'last_name_en',
    'priority',
    'ranking',
    'score',
    'tcas_status',
    'applicant_status',
    'interview_reason',
]

def extract_application_data(application, 
                             major_selections, 
                             admission_results, 
                             admission_projects,
                             personal_profiles,
                             project_majors,
                             admission_round):
    applicant = application.applicant
    project = admission_projects[application.admission_project_id]
    major_selection = major_selections.get(application.id,None)
    if major_selection:
        majors =  major_selection.get_majors(project_majors[project.id])
    else:
        majors = []
    if applicant.has_registered_with_passport():
        nat = applicant.passport_number
    else:
        nat = applicant.national_id

    tcas_data = {}
    is_found = False
    if nat in tcas_data:
        if tcas_data[nat]['status'] == 'found':
            is_found = True
            
            applicant.prefix = tcas_data[nat]['prefix']
            applicant.first_name = tcas_data[nat]['first_name']
            applicant.last_name = tcas_data[nat]['last_name']
        
        
    profile = personal_profiles[applicant.id]
    app_date = '%02d/%02d/%04d' % (application.applied_at.day,
                                   application.applied_at.month,
                                   application.applied_at.year + 543)
    app_type = '1_2569'
    
    results = []
    for m in majors:
        result = None
        cupt_major = {
            'program_id': m.get_detail_items()[-2],
            'major_id': m.get_detail_items()[-1],
            'project_id': project.cupt_code,
        }

        interview_status = '0'
        result = admission_results.get((application.id, m.id), None)
        if result and result.is_accepted:
            interview_status = '1'
        
        results.append(extract_raw_data(
            applicant, application, profile,
            app_date, cupt_major,
            app_type,
            '0','0',
            interview_status,
            '0',
            APPLICANT_FIELDS))

    return results

@valid_token_required
def applicants(request,admission_round_id,project_id=0):
    admission_round = get_object_or_404(AdmissionRound, id=admission_round_id)
    admission_project = get_object_or_404(AdmissionProject, id=project_id)

    applications = (ProjectApplication.objects
                    .filter(admission_project=admission_project,
                            is_canceled=False,
                            cached_has_paid=True)
                    .select_related('applicant')
                    .order_by('applicant__national_id')
                    .all())
    
    admission_projects = {
        p.id: p
        for p in AdmissionProject.objects.all()
    }

    personal_profiles = {
        p.applicant_id: p
        for p in PersonalProfile.objects.all()
    }

    major_selections = { 
        m.project_application_id: m 
        for m in MajorSelection.objects.filter(admission_project=admission_project).all() 
    }

    admission_results = { 
        (r.application_id, r.major_id): r 
        for r in AdmissionResult.objects.filter(admission_project=admission_project).all() 
    }

    project_majors = {
        project_id: {
            major.number: major
            for major in Major.objects.filter(admission_project=admission_projects[project_id]).all()
        }
        for project_id in admission_projects.keys()
    }

    try:
        page = int(request.GET.get('page', 1))
    except:
        page = 1

    PAGE_SIZE = 1000
    page_count = (len(applications) + PAGE_SIZE - 1) // PAGE_SIZE

    applications = applications[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]
    results = []
    for application in applications:
        results += extract_application_data(application, 
                                            major_selections, 
                                            admission_results, 
                                            admission_projects,
                                            personal_profiles,
                                            project_majors,
                                            admission_round)
    data = {
        "applications": results,
        "page": page,
        "size": len(results),
        "total_pages": page_count,
    }
    return HttpResponse(json.dumps(data), content_type="application/json")
