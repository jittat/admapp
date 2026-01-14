import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import Http404, HttpResponse
from django.contrib import messages

from api import models
from backoffice.models import APIToken, AdjustmentMajor, AdjustmentMajorSlot
from appl.models import AdmissionProject, AdmissionRound, Major, Faculty
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

def build_applicant_json(applicant, application, personal_profile, app_date, cupt_major,
                         app_type, tcas_id, ranking, applicant_status, interview_description,
                         admission_round, admission_project, major, faculty,
                         has_confirmed, status, status_description):
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
        'admission_round',
        'project_title',
        'major_number',
        'major_title',
        'faculty',
        'campus',
        'has_confirmed',
        'status',
        'status_description'
    ]

    university_id = '002'

    data = {
        'university_id': university_id,
        'program_id': cupt_major['program_id'],
        'major_id': cupt_major['major_id'],
        'project_id': cupt_major['project_id'],
        'type': app_type,
        'citizen_id': '',
        'title': applicant.prefix,
        'first_name_th': applicant.first_name,
        'last_name_th': applicant.last_name,
        'first_name_en': personal_profile.first_name_english,
        'last_name_en': personal_profile.last_name_english,
        'priority': 0,
        'ranking': ranking,
        'score': 0,
        'tcas_status': 0,
        'applicant_status': applicant_status,
        'interview_reason': '0',

        'admission_round': str(admission_round),
        'project_title': admission_project.title,
        'major_number': major.number,
        'major_title': major.title,
        'faculty': faculty.title,
        'campus': faculty.campus.title,

        'has_confirmed': has_confirmed,
        'status': status,
        'status_description': status_description
    }

    if not applicant.has_registered_with_passport():
        data['citizen_id'] = applicant.national_id
    else:
        data['citizen_id'] = applicant.passport_number

    return { h:data[h] for h in APPLICANT_FIELDS }


def extract_application_data(application, 
                             major_selections, 
                             admission_results, 
                             admission_projects,
                             personal_profiles,
                             project_majors,
                             faculties,
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
    app_type = f'{admission_round.number}_2569'
    
    results = []
    for m in majors:
        result = None
        cupt_major = {
            'program_id': m.get_detail_items()[-2],
            'major_id': m.get_detail_items()[-1],
            'project_id': project.cupt_code,
        }

        applicant_status = '3'
        result = admission_results.get((application.id, m.id), None)
        if result and result.is_accepted:
            applicant_status = '2'
        
        faculty = faculties[m.faculty_id]

        has_confirmed = 0
        if not result:
            status = 1
            status_description = 'สมัคร'
        elif result.has_confirmed:
            status = 4
            status_description = 'รับเข้าศึกษาและยืนยันสิทธิ์'
            has_confirmed = 1
        elif result.is_accepted:
            status = 3
            status_description = 'รับเข้าศึกษา'
        elif result.is_accepted_for_interview:
            status = 2
            status_description = 'เรียกสัมภาษณ์ แต่ไม่รับเข้าศึกษา'
        else:
            status = 1
            status_description = 'สมัคร'

        results.append(build_applicant_json(
            applicant, application, profile,
            app_date, cupt_major,
            app_type,
            '0','0',
            applicant_status,
            '0',
            admission_round,
            project,
            m,
            faculty,
            has_confirmed,
            status,
            status_description))

    return results

@valid_token_required
def applicants(request,admission_round_id,project_id=0):
    admission_round = get_object_or_404(AdmissionRound, id=admission_round_id)

    if project_id == 0:
        admission_project = None
        applications = (ProjectApplication.objects
                        .filter(admission_round=admission_round,
                                is_canceled=False,
                                cached_has_paid=True)
                        .select_related('applicant')
                        .order_by('applicant__national_id')
                        .all())
    else:
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

    if admission_project:
        major_selections = { 
            m.project_application_id: m 
            for m in MajorSelection.objects.filter(admission_project=admission_project).all() 
        }

        admission_results = { 
            (r.application_id, r.major_id): r 
            for r in AdmissionResult.objects.filter(admission_project=admission_project).all() 
        }
    else:
        major_selections = { 
            m.project_application_id: m 
            for m in MajorSelection.objects.filter(admission_round=admission_round).all() 
        }

        admission_results = { 
            (r.application_id, r.major_id): r 
            for r in AdmissionResult.objects.filter(admission_round=admission_round).all() 
        }

    project_majors = {
        project_id: {
            major.number: major
            for major in Major.objects.filter(admission_project=admission_projects[project_id]).all()
        }
        for project_id in admission_projects.keys()
    }

    faculties = {
        f.id: f
        for f in Faculty.objects.all()
    }

    try:
        page = int(request.GET.get('page', 1))
    except:
        page = 1

    PAGE_SIZE = 500
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
                                            faculties,
                                            admission_round)
    data = {
        "applications": results,
        "meta": {
            "page": page,
            "size": len(results),
            "total_pages": page_count,
        },
        "links": {
            "self": request.build_absolute_uri(),
        }
    }
    if page < page_count:
        next_page = page + 1
        data['links']['next'] = f"{request.build_absolute_uri().split('?')[0]}?page={next_page}"
    if page > 1:
        prev_page = page - 1
        data['links']['prev'] = f"{request.build_absolute_uri().split('?')[0]}?page={prev_page}"
    return HttpResponse(json.dumps(data), content_type="application/json")


def build_adjustment_slot_json(major, slots, admission_rounds):
    data = []
    for slot in slots:
        slot_data = {
            "id": slot.id,
            "major_full_code": slot.major_full_code,
            "cupt_code": slot.cupt_code,
            "admission_round_number": slot.admission_round_number,
            "admission_round_title": str(admission_rounds[slot.admission_round_id]),
            "admission_project_title": slot.admission_project_title,

            "original_slots": slot.original_slots,
            "current_slots": slot.current_slots,
            "confirmed_slots": slot.latest_confirmed_slots(),

            "num_confirmed_applications": slot.latest_confirmed_slots(),
        }
        if slot.num_applications != None:
            slot_data['num_applications'] = slot.num_applications
        if slot.num_accepted_applications != None:
            slot_data['num_accepted_applications'] = slot.num_accepted_applications
        data.append(slot_data)
    return data


@valid_token_required
def admission_slot_stats(request, year):
    if year != 2569:
        return HttpResponse(json.dumps([]), 
                            content_type="application/json")
    
    try:
        page = int(request.GET.get('page', 1))
    except:
        page = 1

    adjustment_majors = AdjustmentMajor.objects.all()

    PAGE_SIZE = 500
    page_count = (len(adjustment_majors) + PAGE_SIZE - 1) // PAGE_SIZE

    adjustment_majors = adjustment_majors[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]

    faculties = {
        f.id: f
        for f in Faculty.objects.all()
    }

    all_slots = {}
    for slot in AdjustmentMajorSlot.objects.all():
        if slot.adjustment_major_id not in all_slots:
            all_slots[slot.adjustment_major_id] = []
        all_slots[slot.adjustment_major_id].append(slot)

    admission_rounds = {
        r.id: r
        for r in AdmissionRound.objects.all()
    }

    results = []
    for major in adjustment_majors:
        major_slots = build_adjustment_slot_json(major, 
                                                 all_slots.get(major.id, []), 
                                                 admission_rounds)
        major_data = {
            "program_id": major.get_program_id(),
            "major_id": major.get_major_id(),
            "full_code": major.full_code,
            "study_type_code": major.study_type_code,
            "title": major.title,
            "faculty": faculties[major.faculty_id].title,
            "campus": faculties[major.faculty_id].campus.title,
            "id": major.id,
            "slots": major_slots,
        }
        results.append(major_data)

    data = {
        "majors": results,
        "meta": {
            "page": page,
            "size": len(results),
            "total_pages": page_count,
        },
        "links": {
            "self": request.build_absolute_uri(),
        }
    }
    if page < page_count:
        next_page = page + 1
        data['links']['next'] = f"{request.build_absolute_uri().split('?')[0]}?page={next_page}"
    if page > 1:
        prev_page = page - 1
        data['links']['prev'] = f"{request.build_absolute_uri().split('?')[0]}?page={prev_page}"
    return HttpResponse(json.dumps(data), content_type="application/json")
