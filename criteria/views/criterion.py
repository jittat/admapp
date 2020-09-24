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


@user_login_required
def project_index(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('criteria:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
        admission_criterias = AdmissionCriteria.objects.filter(
            admission_project_id=project_id, faculty_id=faculty.id)
    else:
        faculty = None
        admission_criterias = AdmissionCriteria.objects.filter(
            admission_project_id=project_id)
    notice = request.session.pop('notice', None)

    return render(request,
                  'criterion/index.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'admission_criterias': admission_criterias,
                   'notice': notice
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
            if value.isnumeric():
                value = Decimal(value)

            score_criteria_dict[data_key][splitted_keys[2]
                                          ] = value
        elif splitted_keys[0] == "majors":
            data_key = splitted_keys[0]+'_'+splitted_keys[1]
            if data_key not in selected_major_dict:
                selected_major_dict[data_key] = dict()
            value = post_request[key]
            if value.isnumeric():
                value = Decimal(value)
            selected_major_dict[data_key][splitted_keys[2]] = value

    with transaction.atomic():

        if admission_criteria is None:
            admission_criteria = AdmissionCriteria(
                admission_project=project, version=version, faculty=faculty)
            admission_criteria.save()
        else:
            admission_criteria.scorecriteria_set.all().delete()
            admission_criteria.curriculummajoradmissioncriteria_set.all().delete()
            version = admission_criteria.version + 1
            admission_criteria.version = version
            admission_criteria.save()

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
            for s in secondary_scoring_criterias:
                print(s)
                criteria_order = s.primary_order - 1
                s.parent = primary_scoring_criterias[criteria_order]

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

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
    else:
        faculty = None

    majors = CurriculumMajor.objects.filter(
        admission_project_id=project_id).select_related('cupt_code')

    if faculty:
        majors = [m for m in majors if m.faculty_id == faculty.id]

    if request.method == 'POST':
        upsert_admission_criteria(
            request.POST, project=project, faculty=faculty)

        request.session['notice'] = "สร้างเกณฑ์ใหม่ สำเร็จ"
        return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]), is_complete=True)

        # return render(request, 'criterion/complete.html', {'project': project, 'admission_round': admission_round})

    return render(request,
                  'criterion/create.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': json.dumps([dict({"id": m.id, "title": ("%s (%s) %s") % (m.cupt_code.title, m.cupt_code.program_type, m.cupt_code.major_title)}) for m in sorted(majors, key=(lambda m: (m.cupt_code.program_code, m.cupt_code.major_title)))]),
                   })


# TODO: get real data
@user_login_required
def edit(request, project_id, round_id, criteria_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)
    admission_criteria = get_object_or_404(AdmissionCriteria, pk=criteria_id)

    if not can_user_view_project(user, project):
        return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
    else:
        faculty = None

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
        return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]), is_complete=True)

    score_criterias = admission_criteria.scorecriteria_set.filter(
        secondary_order=0)
    selected_major = admission_criteria.curriculummajoradmissioncriteria_set.all()

    data_criteria = [
        [{
            "id": str(s.primary_order),
            "title": s.description,
            "value": float(s.value),
            "unit": s.unit,
            "children": [{
                "id": "%s.%s" % (ss.primary_order, ss.secondary_order),
                "title": ss.description,
                "value": float(ss.value),
                "unit": ss.unit
            } for ss in s.childs.all()]
        }, s.criteria_type] for s in score_criterias
    ]

    data_required = [d[0] for d in data_criteria if d[1] == "required"]

    data_scoring = [d[0] for d in data_criteria if d[1] == "scoring"]

    data_selected_majors = [
        {
            "id": m.curriculum_major.id,
            "title": m.curriculum_major.cupt_code.title,
            "slot": int(m.slots)
        } for m in selected_major
    ]

    return render(request,
                  'criterion/edit.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': json.dumps([dict({"id": m.id, "title": ("%s (%s) %s") % (m.cupt_code.title, m.cupt_code.program_type, m.cupt_code.major_title)}) for m in sorted(majors, key=(lambda m: (m.cupt_code.program_code, m.cupt_code.major_title)))]),
                   'data_required': json.dumps(data_required),
                   'data_scoring': json.dumps(data_scoring),
                   'data_selected_majors': json.dumps(data_selected_majors)
                   })


@user_login_required
def select_curriculum_major(request, project_id, round_id, code_id=0, value='none'):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('criteria:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
    else:
        faculty = None

    major_choices = MajorCuptCode.objects.filter(faculty=faculty)

    curriculum_majors = CurriculumMajor.objects.filter(admission_project_id=project_id,
                                                       faculty=faculty).all()

    selected_curriculum_majors = dict(
        [(m.cupt_code_id, m) for m in curriculum_majors])
    for major in major_choices:
        major.is_selected = major.id in selected_curriculum_majors
        if major.is_selected:
            major.can_be_deleted = not selected_curriculum_majors[major.id].is_with_some_admission_criteria(
            )

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
                  'criterion/select_curriculum_majors.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'major_choices': major_choices,
                   })
