import csv
import json
from decimal import Decimal

from datetime import datetime
from django.core import serializers

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.db import transaction

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionRound
from appl.models import ProjectApplication, Payment, Major, AdmissionResult, Faculty
from appl.models import ProjectUploadedDocument, UploadedDocument, ExamScoreProvider, MajorInterviewDescription

from backoffice.views.permissions import can_user_view_project, can_user_view_applicant_in_major, can_user_view_applicants_in_major
from backoffice.decorators import user_login_required

from criteria.models import CurriculumMajor, AdmissionCriteria, ScoreCriteria, CurriculumMajorAdmissionCriteria, MajorCuptCode

def is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def get_all_curriculum_majors(project, faculty=None):
    if not faculty:
        majors = CurriculumMajor.objects.filter(
            admission_project_id=project.id).select_related('cupt_code')
    else:
        majors = CurriculumMajor.objects.filter(
            admission_project_id=project.id,
            faculty_id=faculty.id).select_related('cupt_code')

    return majors

def get_user_faculty_choices(user):
    if (not user.profile.is_admission_admin) and (not user.profile.is_campus_admin):
        return []
    else:
        if user.profile.is_campus_admin:
            return Faculty.objects.filter(campus_id=user.profile.campus_id)
        else:
            return Faculty.objects.all()

def extract_user_faculty(request, user):
    faculty_choices = get_user_faculty_choices(user)
    if (not user.profile.is_admission_admin) and (not user.profile.is_campus_admin):
        faculty = user.profile.faculty
    elif user.profile.is_campus_admin:
        if request.GET.get('faculty_id', None) != None:
            faculty = get_object_or_404(Faculty, pk=request.GET['faculty_id'])
            if faculty.campus_id != user.profile.campus_id:
                return None, faculty_choices
        else:
            faculty = faculty_choices[0]
    else:
        if request.GET.get('faculty_id', None) != None:
            faculty = get_object_or_404(Faculty, pk=request.GET['faculty_id'])
        else:
            faculty = faculty_choices[0]

    return faculty, faculty_choices

@user_login_required
def project_index(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('backoffice:index'))

    faculty, faculty_choices = extract_user_faculty(request, user)

    admission_criterias = AdmissionCriteria.objects.filter(admission_project_id=project_id,
                                                           faculty_id=faculty.id,
                                                           is_deleted=False)
    notice = request.session.pop('notice', None)

    curriculum_majors = get_all_curriculum_majors(project, faculty)
    curriculum_majors_with_criterias = []
    for criteria in admission_criterias:
        curriculum_majors_with_criterias += criteria.curriculummajor_set.all()
    curriculum_majors_with_criteria_ids = set([m.id for m
                                               in curriculum_majors_with_criterias])

    free_curriculum_majors = [m for m in curriculum_majors
                              if m.id not in curriculum_majors_with_criteria_ids]

    return render(request,
                  'criteria/index.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'faculty_url_query': '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id),
                   'faculty_choices': faculty_choices,
                   'admission_criterias': admission_criterias,
                   'notice': notice,
                   'free_curriculum_majors': free_curriculum_majors,
                   })


def upsert_admission_criteria(post_request, project=None, faculty=None, admission_criteria=None):
    score_criteria_dict = dict()
    selected_major_dict = dict()
    for key in post_request:
        splitted_keys = key.split('_')
        if splitted_keys[0] == "required" or splitted_keys[0] == "scoring":
            data_key = splitted_keys[0]+'_'+splitted_keys[1]
            if data_key not in score_criteria_dict:
                order_numbers = splitted_keys[1].split('.')
                initial_data = {
                    "criteria_type": splitted_keys[0],
                    "primary_order": int(order_numbers[0]),
                    "secondary_order": 0
                }
                if len(order_numbers) == 2:
                    initial_data["secondary_order"] = int(order_numbers[1])

                score_criteria_dict[data_key] = initial_data

            value = post_request[key]
            if is_number(value):
                value = Decimal(value)

            score_criteria_dict[data_key][splitted_keys[2]
                                          ] = value
        elif splitted_keys[0] == "majors":
            data_key = splitted_keys[0]+'_'+splitted_keys[1]
            if data_key not in selected_major_dict:
                selected_major_dict[data_key] = dict()
            value = post_request[key]
            if is_number(value):
                value = Decimal(value)
            selected_major_dict[data_key][splitted_keys[2]] = value

    with transaction.atomic():

        if admission_criteria is None:
            version = 1
            admission_criteria = AdmissionCriteria(
                admission_project=project,
                version=version,
                faculty=faculty)
            admission_criteria.save()
        else:
            old_admission_criteria = admission_criteria
            version = old_admission_criteria.version + 1

            admission_criteria = AdmissionCriteria(
                admission_project=old_admission_criteria.admission_project,
                faculty=admission_criteria.faculty,
                version=version)
            admission_criteria.save()

            old_admission_criteria.is_deleted = True
            old_admission_criteria.save()

        scoring_criterias = [ScoreCriteria(
            admission_criteria=admission_criteria,
            version=version,
            primary_order=s["primary_order"],
            secondary_order=s["secondary_order"],
            criteria_type=s["criteria_type"],
            score_type="OTHER",
            value=s["value"] if isinstance(s["value"], Decimal) else None,
            unit=(s["unit"] if "unit" in s else ""),
            description=s["title"] if "title" in s else None,
            relation=s["relation"] if "relation" in s else None,
        ) for _, s in score_criteria_dict.items()]

        primary_scoring_criterias = sorted(
            [s for s in scoring_criterias if s.secondary_order == 0], key=lambda s: s.primary_order)

        secondary_scoring_criterias = [
            s for s in scoring_criterias if s.secondary_order != 0]

        ScoreCriteria.objects.bulk_create(
            primary_scoring_criterias)

        with transaction.atomic():
            primary_scoring_criterias = ScoreCriteria.objects.filter(
                admission_criteria=admission_criteria)
            primary_scoring_criteria_map = dict()

            for p in primary_scoring_criterias:
                primary_scoring_criteria_map["%s_%s" % (
                    p.criteria_type, p.primary_order)] = p

            for s in secondary_scoring_criterias:
                s.parent = primary_scoring_criteria_map["%s_%s" % (
                    s.criteria_type, s.primary_order)]

            ScoreCriteria.objects.bulk_create(
                secondary_scoring_criterias)

        major_criterias = [CurriculumMajorAdmissionCriteria(
            admission_criteria=admission_criteria,
            curriculum_major_id=m['id'],
            slots=m['slot']
        ) for _, m in selected_major_dict.items()]
        CurriculumMajorAdmissionCriteria.objects.bulk_create(
            major_criterias)


@user_login_required
def create(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]))

    faculty, faculty_choices = extract_user_faculty(request, user)
    majors = get_all_curriculum_majors(project, faculty)

    if request.method == 'POST':
        upsert_admission_criteria(
            request.POST, project=project, faculty=faculty)

        request.session['notice'] = "สร้างเกณฑ์ใหม่ สำเร็จ"

        faculty_url_query = '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id)

        return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]) + faculty_url_query, is_complete=True)

        # return render(request, 'criterion/complete.html', {'project': project, 'admission_round': admission_round})

    data_required = []
    data_scoring = []
    data_selected_majors = []

    duplicate_score_id = request.GET.get('duplicate_score_id', None)
    selected_major_id = request.GET.get('selected_major_id', None)

    if duplicate_score_id is not None:
        score_criterias = get_object_or_404(
            AdmissionCriteria, pk=duplicate_score_id).scorecriteria_set.filter(secondary_order=0)
        data_criteria = [
            [{
                "id": str(s.primary_order),
                "title": s.description,
                "value": float(s.value) if s.value is not None else None,
                "unit": s.unit,
                "relation": s.relation if s.relation is not None else None,
                "children": [{
                    "id": "%s.%s" % (ss.primary_order, ss.secondary_order),
                    "title": ss.description,
                    "value": float(ss.value) if ss.value is not None else None,
                    "unit": ss.unit
                } for ss in s.childs.all()]
            }, s.criteria_type] for s in score_criterias
        ]

        data_required = [d[0] for d in data_criteria if d[1] == "required"]
        data_scoring = [d[0] for d in data_criteria if d[1] == "scoring"]
    if selected_major_id is not None:
        preselected_major = get_object_or_404(
            CurriculumMajor, pk=selected_major_id)
        data_selected_majors = [
            {
                "id": preselected_major.id,
                "title": ("%s (%s) %s") % (preselected_major.cupt_code.title,  preselected_major.cupt_code.program_type,  preselected_major.cupt_code.major_title),
            }
        ]

    return render(request,
                  'criteria/create.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': json.dumps([dict({"id": m.id, "title": ("%s (%s) %s") % (m.cupt_code.title, m.cupt_code.program_type, m.cupt_code.major_title)}) for m in sorted(majors, key=(lambda m: (m.cupt_code.program_code, m.cupt_code.major_title)))]),
                   'data_required': json.dumps(data_required),
                   'data_scoring': json.dumps(data_scoring),
                   'data_selected_majors': json.dumps(data_selected_majors)
                   })


@user_login_required
def edit(request, project_id, round_id, criteria_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)
    admission_criteria = get_object_or_404(AdmissionCriteria, pk=criteria_id)

    if not can_user_view_project(user, project):
        return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]))

    faculty, faculty_choices = extract_user_faculty(request, user)
    if admission_criteria.admission_project.id != project_id or (not user.profile.is_admission_admin and faculty.id != admission_criteria.faculty.id):
        return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]))

    majors = CurriculumMajor.objects.filter(
        admission_project_id=project_id).select_related('cupt_code')

    if faculty:
        majors = [m for m in majors if m.faculty_id == faculty.id]

    if request.method == 'POST':
        upsert_admission_criteria(
            request.POST, admission_criteria=admission_criteria)

        request.session['notice'] = "แก้ไขเกณฑ์ สำเร็จ"

        faculty_url_query = '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id)

        return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]) + faculty_url_query, is_complete=True)

    score_criterias = admission_criteria.scorecriteria_set.filter(
        secondary_order=0)
    selected_majors = admission_criteria.curriculummajoradmissioncriteria_set.all()

    data_criteria = [
        [{
            "id": str(s.primary_order),
            "title": s.description,
            "value": float(s.value) if s.value is not None else None,
            "unit": s.unit,
            "relation": s.relation if s.relation is not None else None,
            "children": [{
                "id": "%s.%s" % (ss.primary_order, ss.secondary_order),
                "title": ss.description,
                "value": float(ss.value) if ss.value is not None else None,
                "unit": ss.unit
            } for ss in s.childs.all()]
        }, s.criteria_type] for s in score_criterias
    ]

    data_required = [d[0] for d in data_criteria if d[1] == "required"]

    data_scoring = [d[0] for d in data_criteria if d[1] == "scoring"]

    data_selected_majors = [
        {
            "id": m.curriculum_major.id,
            "title": ("%s (%s) %s") % (m.curriculum_major.cupt_code.title,  m.curriculum_major.cupt_code.program_type,  m.curriculum_major.cupt_code.major_title),
            "slot": int(m.slots)
        } for m in selected_majors
    ]

    return render(request,
                  'criteria/edit.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': json.dumps([dict({"id": m.id, "title": ("%s (%s) %s") % (m.cupt_code.title, m.cupt_code.program_type, m.cupt_code.major_title)}) for m in sorted(majors, key=(lambda m: (m.cupt_code.program_code, m.cupt_code.major_title)))]),
                   'data_required': json.dumps(data_required),
                   'data_scoring': json.dumps(data_scoring),
                   'data_selected_majors': json.dumps(data_selected_majors)
                   })


@user_login_required
def delete(request, project_id, round_id, criteria_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)
    admission_criteria = get_object_or_404(AdmissionCriteria, pk=criteria_id)

    if not can_user_view_project(user, project):
        return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]))

    faculty, faculty_choices = extract_user_faculty(request, user)
    if admission_criteria.admission_project.id != project_id or (not user.profile.is_admission_admin and faculty.id != admission_criteria.faculty.id):
        return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]))

    if request.method == 'POST':
        admission_criteria.is_deleted = True
        admission_criteria.save()

        request.session['notice'] = "ลบเกณฑ์ สำเร็จ"

    faculty_url_query = '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id)

    return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]) + faculty_url_query)


@user_login_required
def select_curriculum_majors(request, project_id, round_id, code_id=0, value='none'):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('backoffice:index'))

    faculty, faculty_choices = extract_user_faculty(request, user)
    major_choices = MajorCuptCode.objects.filter(faculty=faculty)

    curriculum_majors = CurriculumMajor.objects.filter(admission_project_id=project_id,
                                                       faculty=faculty).all()

    selected_curriculum_majors = dict(
        [(m.cupt_code_id, m) for m in curriculum_majors])
    for major in major_choices:
        major.is_selected = major.id in selected_curriculum_majors
        if major.is_selected:
            major.can_be_deleted = not selected_curriculum_majors[major.id].is_with_some_admission_criteria()

    if request.method == 'POST':
        major_cupt_codes = [m for m in major_choices if m.id == int(code_id)]
        if len(major_cupt_codes) != 1:
            return HttpResponseNotFound()
        major_cupt_code = major_cupt_codes[0]

        if value == 'select':
            curriculum_major = CurriculumMajor(admission_project=project,
                                               cupt_code=major_cupt_code,
                                               faculty=faculty)
            curriculum_major.save()
            return HttpResponse('true')
        elif value == 'unselect':
            if not major_cupt_code.is_selected or (not major_cupt_code.can_be_deleted):
                return HttpResponseForbidden()
            curriculum_major = selected_curriculum_majors[major_cupt_code.id]
            curriculum_major.delete()
            return HttpResponse('false')
        return HttpResponseNotFound()

    return render(request,
                  'criteria/select_curriculum_majors.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'faculty_url_query': '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id),
                   'faculty_choices': faculty_choices,
                   'major_choices': major_choices,
                   })


@user_login_required
def list_curriculum_majors(request):
    user = request.user

    admission_rounds = AdmissionRound.objects.all()

    faculty, faculty_choices = extract_user_faculty(request, user)
    major_choices = MajorCuptCode.objects.filter(faculty=faculty)
    curriculum_majors = CurriculumMajor.objects.filter(faculty=faculty).all()
    if not user.profile.is_admission_admin:
        admission_projects = user.profile.admission_projects.filter(
            is_available=True).all()
    else:
        admission_projects = AdmissionProject.objects.filter(is_available=True)

    for p in admission_projects:
        p.adm_rounds = set([r.id for r in p.admission_rounds.all()])

    major_table = []
    project_lists = []

    for r in admission_rounds:
        round_table = []
        for m in major_choices:
            row = []
            for p in admission_projects:
                if r.id in p.adm_rounds:
                    row.append(False)
            round_table.append(row)

        c = 0
        for p in admission_projects:
            if r.id in p.adm_rounds:
                cmajor_set = set([cm.cupt_code_id for cm in curriculum_majors
                                  if cm.admission_project_id == p.id])
                for m, i in zip(major_choices, range(len(major_choices))):
                    round_table[i][c] = m.id in cmajor_set

                c += 1

        project_lists.append(
            [p for p in admission_projects if r.id in p.adm_rounds])
        major_table.append(zip(major_choices, round_table))

    return render(request,
                  'criteria/list_curriculum_majors.html',
                  {'admission_rounds': admission_rounds,
                   'faculty': faculty,
                   'faculty_url_query': '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id),
                   'faculty_choices': faculty_choices,
                   'major_choices': major_choices,
                   'project_lists': project_lists,
                   'major_table': major_table,
                   'round_data': list(zip(admission_rounds, major_table, project_lists)),
                   })
