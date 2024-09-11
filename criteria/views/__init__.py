import json
from decimal import Decimal

from django.db import transaction
from django.http import Http404
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from appl.models import AdmissionProject, AdmissionRound
from appl.models import Faculty
from backoffice.decorators import user_login_required
from backoffice.views.permissions import can_user_view_project
from criteria.models import AdmissionCriteria, ScoreCriteria, CurriculumMajorAdmissionCriteria, \
    MajorCuptCode, CurriculumMajor, AdmissionProjectFacultyInterviewDate


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
        if request.GET.get('faculty_id', None) is not None:
            faculty = get_object_or_404(Faculty, pk=request.GET['faculty_id'])
            if faculty.campus_id != user.profile.campus_id:
                return None, faculty_choices
        else:
            faculty = faculty_choices[0]
    else:
        if request.GET.get('faculty_id', None) is not None:
            faculty = get_object_or_404(Faculty, pk=request.GET['faculty_id'])
        else:
            faculty = faculty_choices[0]

    return faculty, faculty_choices


def sort_admission_criteria_rows(admission_criteria_rows):
    lst = []
    for criteria in admission_criteria_rows:
        first_criteria = criteria['criterias'][0]
        key = '-'.join([mc.curriculum_major.cupt_code.program_code + mc.curriculum_major.cupt_code.major_code for mc in
                        criteria['majors']])
        total_slots = sum([mc.slots for mc in criteria['majors']])
        lst.append((first_criteria.faculty_id, key, -total_slots, first_criteria.id, criteria))

    return [item[4] for item in sorted(lst)]


def combine_criteria_rows(rows):
    major_slots = {}

    for r in rows:
        curriculum_major_admission_criterias = r['majors']
        for mc in curriculum_major_admission_criterias:
            major = mc.curriculum_major
            major_id = mc.curriculum_major.id
            if major_id not in major_slots:
                major_slots[major_id] = []
            major_slots[major_id].append((mc.slots, mc, r['criterias'][0]))

    combined_rows = []
    deleted_major_ids = set()

    for major_id in major_slots:
        slots = major_slots[major_id]
        if len(slots) > 1:
            non_zero_mc = [s for s in slots if s[0] > 0]
            if len(non_zero_mc) == 1:
                combined_rows.append({
                    'majors': [non_zero_mc[0][1]],
                    'criterias': [s[2] for s in slots],
                    'major_count': 1,
                    'criteria_count': len(slots),
                })

                for _, mc, _ in slots:
                    deleted_major_ids.add(mc.id)

    output_rows = []

    for r in rows:
        curriculum_major_admission_criterias = r['majors']
        output_majors = []
        for mc in curriculum_major_admission_criterias:
            if mc.id not in deleted_major_ids:
                output_majors.append(mc)

        if len(output_majors) != 0:
            output_rows.append({
                'majors': output_majors,
                'criterias': r['criterias'],
                'major_count': len(output_majors),
                'criteria_count': len(r['criterias']),
            })

    return output_rows + combined_rows


def prepare_admission_criteria(admission_criterias, curriculum_majors, combine_majors=False):
    curriculum_majors_with_criterias = []
    # curriculum_major_criterias = { cm.id:[] for cm in curriculum_majors }

    faculty_interview_date_cache = {} 
    
    for criteria in admission_criterias:
        criteria.cache_score_criteria_children()
        criteria.curriculum_major_admission_criterias = criteria.curriculummajoradmissioncriteria_set.select_related(
            'curriculum_major').all()
        criteria.curriculum_major_admission_criteria_count = len(criteria.curriculum_major_admission_criterias)
        criteria.curriculum_majors = [mj.curriculum_major for mj in criteria.curriculum_major_admission_criterias]
        curriculum_majors_with_criterias += criteria.curriculum_majors

        # for cm in criteria.curriculum_majors:
        #    curriculum_major_criterias[cm.id].append((cm,criteria))

    curriculum_majors_with_criteria_ids = set([m.id for m
                                               in curriculum_majors_with_criterias])

    free_curriculum_majors = [m for m in curriculum_majors
                              if m.id not in curriculum_majors_with_criteria_ids]

    admission_criteria_rows = [{'majors': c.curriculum_major_admission_criterias,
                                'criterias': [c],
                                'major_count': len(c.curriculum_major_admission_criterias),
                                'criteria_count': len([c])} for c in admission_criterias]

    if combine_majors:
        admission_criteria_rows = combine_criteria_rows(admission_criteria_rows)

    # add faculty interview date
    for r in admission_criteria_rows:
        first_criteria = r['criterias'][0]
        faculty_id = first_criteria.faculty_id
        if faculty_id not in faculty_interview_date_cache:
            faculty_interview_date_cache[faculty_id] = AdmissionProjectFacultyInterviewDate.get_from(first_criteria.admission_project,
                                                                                                     first_criteria.faculty)
        first_criteria.faculty_interview_date = faculty_interview_date_cache[faculty_id]

    # for row in admission_criteria_rows:
    #    for cmc in row['majors']:
    #        if (cmc.curriculum_major_id in curriculum_major_criterias) and (len(curriculum_major_criterias[cmc.curriculum_major_id]) > 1):
    #            print(cmc.curriculum_major.cupt_code)

    return sort_admission_criteria_rows(admission_criteria_rows), free_curriculum_majors


@user_login_required
def project_index(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)

    if not can_user_view_project(user, project):
        return redirect(reverse('backoffice:index'))

    faculty, faculty_choices = extract_user_faculty(request, user)

    project_faculty_interview_date = AdmissionProjectFacultyInterviewDate.get_from(project, faculty)
    
    admission_criterias = AdmissionCriteria.objects.filter(admission_project_id=project_id,
                                                           faculty_id=faculty.id,
                                                           is_deleted=False)
    notice = request.session.pop('notice', None)

    curriculum_majors = get_all_curriculum_majors(project, faculty)
    admission_criteria_rows, free_curriculum_majors = prepare_admission_criteria(admission_criterias, curriculum_majors)

    return render(request,
                  'criteria/index.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'faculty_url_query': '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id),
                   'faculty_choices': faculty_choices,

                   'project_faculty_interview_date': project_faculty_interview_date,
                   
                   'admission_criteria_rows': admission_criteria_rows,
                   'notice': notice,
                   'free_curriculum_majors': free_curriculum_majors,
                   })


@user_login_required
def project_report(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)

    if not user.profile.is_admission_admin:
        return redirect(reverse('backoffice:index'))

    admission_criterias = (AdmissionCriteria
                           .objects
                           .filter(admission_project_id=project_id,
                                   is_deleted=False)
                           .order_by('faculty_id'))

    curriculum_majors = get_all_curriculum_majors(project)
    admission_criteria_rows, free_curriculum_majors = prepare_admission_criteria(admission_criterias, curriculum_majors,
                                                                                 True)

    return render(request,
                  'criteria/report_index.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'admission_criteria_rows': admission_criteria_rows,
                   'free_curriculum_majors': free_curriculum_majors,
                   })


def extract_custom_interview_date(post_request):
    from datetime import date

    custom_interview_date = None
    if 'custom_interview_date' in post_request:
        if post_request['custom_interview_date']!='0':
            custom_interview_date = date.fromisoformat(post_request['custom_interview_date'])
    return custom_interview_date


def extract_additional_interview_condition(post_request):
    additional_interview_condition = ''
    if 'additional_interview_condition' in post_request:
        additional_interview_condition = post_request['additional_interview_condition'].strip()
    return additional_interview_condition


def upsert_admission_criteria(post_request, project=None, faculty=None, admission_criteria=None, user=None):
    score_criteria_dict = dict()
    selected_major_dict = dict()
    for key in post_request:
        splitted_keys = key.split('_')
        if splitted_keys[0] == "required" or splitted_keys[0] == "scoring":
            data_key = splitted_keys[0] + '_' + splitted_keys[1]
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
            data_key = splitted_keys[0] + '_' + splitted_keys[1]
            if data_key not in selected_major_dict:
                selected_major_dict[data_key] = dict()
            value = post_request[key]
            if is_number(value):
                value = Decimal(value)
            selected_major_dict[data_key][splitted_keys[2]] = value

    additional_interview_condition = extract_additional_interview_condition(post_request)
    custom_interview_date = extract_custom_interview_date(post_request)

    if (len(selected_major_dict) == 0) and (len(score_criteria_dict) == 0):
        raise Http404("Error ")

    with transaction.atomic():

        if admission_criteria is None:
            version = 1
            admission_criteria = AdmissionCriteria(
                additional_interview_condition=additional_interview_condition,
                interview_date=custom_interview_date,
                admission_project=project,
                version=version,
                faculty=faculty)
            admission_criteria.save()
            old_admission_criteria = None
        else:
            old_admission_criteria = admission_criteria
            version = old_admission_criteria.version + 1

            admission_criteria = AdmissionCriteria(
                admission_project=old_admission_criteria.admission_project,
                faculty=admission_criteria.faculty,
                additional_description=old_admission_criteria.additional_description,
                additional_condition=old_admission_criteria.additional_condition,
                accepted_student_curriculum_type_flags=old_admission_criteria.accepted_student_curriculum_type_flags,
                additional_interview_condition=additional_interview_condition,
                interview_date=custom_interview_date,
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
            score_type=s["type"] if "type" in s else "OTHER",
            value=s["value"] if "value" in s and isinstance(s["value"], Decimal) else None,
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

        if old_admission_criteria is not None:
            old_major_criterias = CurriculumMajorAdmissionCriteria.objects.filter(
                admission_criteria=old_admission_criteria).all()
            add_limits = {}
            for m in old_major_criterias:
                add_limits[m.curriculum_major_id] = m.add_limit
            for m in major_criterias:
                if m.curriculum_major_id in add_limits:
                    m.add_limit = add_limits[m.curriculum_major_id]

        CurriculumMajorAdmissionCriteria.objects.bulk_create(
            major_criterias)

        if user:
            admission_criteria.created_by = user.username
        admission_criteria.save_curriculum_majors(major_criterias)


@user_login_required
def create(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)

    if not can_user_view_project(user, project):
        return redirect_to_project_index(project_id, round_id)

    faculty, faculty_choices = extract_user_faculty(request, user)
    majors = get_all_curriculum_majors(project, faculty)

    if request.method == 'POST':
        return handle_create_criteria(faculty, faculty_choices, project, project_id, request, round_id, user)

    return render_create_criteria(admission_round, faculty, majors, project, request)


def render_create_criteria(admission_round, faculty, majors, project, request):
    data_required = []
    data_scoring = []
    data_selected_majors = []
    duplicate_score_id = request.GET.get('duplicate_score_id', None)
    selected_major_id = request.GET.get('selected_major_id', None)
    additional_interview_condition = ''
    if duplicate_score_id is not None:
        admission_criteria = get_object_or_404(AdmissionCriteria,
                                               pk=duplicate_score_id)
        score_criterias = admission_criteria.scorecriteria_set.filter(secondary_order=0)
        additional_interview_condition = admission_criteria.additional_interview_condition
        data_criteria = [
            [{
                "id": str(s.primary_order),
                "title": s.description,
                "value": float(s.value) if s.value is not None else None,
                "unit": s.unit,
                "relation": s.relation if s.relation is not None else None,
                "score_type": s.score_type,
                "children": [{
                    "id": "%s.%s" % (ss.primary_order, ss.secondary_order),
                    "title": ss.description,
                    "value": float(ss.value) if ss.value is not None else None,
                    "unit": ss.unit,
                    "score_type": ss.score_type,
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
                "title": ("%s (%s) %s") % (preselected_major.cupt_code.title, preselected_major.cupt_code.program_type,
                                           preselected_major.cupt_code.major_title),
            }
        ]
    # TODO: remove component weights (no more TCAS round 3 - Admission 2)
    uses_component_weights = False
    component_weight_type_choices = CurriculumMajor.get_component_weight_type_choices_unique(majors)

    faculty_interview_date = AdmissionProjectFacultyInterviewDate.get_from(project, faculty)
    
    return render(request,
                  'criteria/create.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': json.dumps([dict({"id": m.id, "title": ("%s (%s) %s") % (
                       m.cupt_code.title, m.cupt_code.program_type, m.cupt_code.major_title)}) for m in
                                         sorted(majors, key=(
                                             lambda m: (m.cupt_code.program_code, m.cupt_code.major_title)))]),
                   'uses_component_weights': uses_component_weights,
                   'component_weight_type_choices': component_weight_type_choices,

                   'data_required': json.dumps(data_required),
                   'data_scoring': json.dumps(data_scoring),
                   'data_selected_majors': json.dumps(data_selected_majors),

                   'faculty_interview_date': faculty_interview_date,
                   'additional_interview_condition': additional_interview_condition,
                   })


def handle_create_criteria(faculty, faculty_choices, project, project_id, request, round_id, user):
    if (not project.is_criteria_edit_allowed) and (not user.is_super_admin):
        return HttpResponseForbidden()

    upsert_admission_criteria(
        request.POST, project=project, faculty=faculty,
        user=user)

    request.session['notice'] = "สร้างเกณฑ์ใหม่ สำเร็จ"
    faculty_url_query = '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id)

    return redirect_to_project_index_with_query(faculty_url_query, project_id, round_id)


def redirect_to_project_index(project_id, round_id):
    return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]))


@user_login_required
def edit(request, project_id, round_id, criteria_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    admission_criteria = get_object_or_404(AdmissionCriteria, pk=criteria_id)

    if not can_user_view_project(user, project):
        return redirect_to_project_index(project_id, round_id)

    faculty, faculty_choices = extract_user_faculty(request, user)
    if admission_criteria.admission_project.id != project_id or (
            not user.profile.is_admission_admin and faculty.id != admission_criteria.faculty.id):
        return redirect_to_project_index(project_id, round_id)

    majors = CurriculumMajor.objects.filter(
        admission_project_id=project_id).select_related('cupt_code')

    if faculty:
        majors = [m for m in majors if m.faculty_id == faculty.id]

    if request.method == 'POST':
        return handle_edit_criteria(admission_criteria, faculty, faculty_choices, request, user, project_id, round_id,
                                    project)

    return render_edit_criteria(admission_criteria, admission_round, faculty, majors, project, request)


def render_edit_criteria(admission_criteria, admission_round, faculty, majors, project, request):
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
            "score_type": s.score_type,
            "children": [{
                "id": "%s.%s" % (ss.primary_order, ss.secondary_order),
                "title": ss.description,
                "value": float(ss.value) if ss.value is not None else None,
                "unit": ss.unit,
                "score_type": ss.score_type,
            } for ss in s.childs.all()]
        }, s.criteria_type] for s in score_criterias
    ]
    data_required = [d[0] for d in data_criteria if d[1] == "required"]
    data_scoring = [d[0] for d in data_criteria if d[1] == "scoring"]
    data_selected_majors = [
        {
            "id": m.curriculum_major.id,
            "title": ("%s (%s) %s") % (m.curriculum_major.cupt_code.title, m.curriculum_major.cupt_code.program_type,
                                       m.curriculum_major.cupt_code.major_title),
            "slot": int(m.slots)
        } for m in selected_majors
    ]
    # TODO: remove component weights (no more TCAS round 3 - Admission 2)
    uses_component_weights = False
    component_weight_type_choices = CurriculumMajor.get_component_weight_type_choices_unique(majors)

    faculty_interview_date = AdmissionProjectFacultyInterviewDate.get_from(project, faculty)
    
    return render(request,
                  'criteria/edit.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': json.dumps([dict({"id": m.id, "title": ("%s (%s) %s") % (
                       m.cupt_code.title, m.cupt_code.program_type, m.cupt_code.major_title)}) for m in
                                         sorted(majors, key=(
                                             lambda m: (m.cupt_code.program_code, m.cupt_code.major_title)))]),

                   'uses_component_weights': uses_component_weights,
                   'component_weight_type_choices': component_weight_type_choices,

                   'data_required': json.dumps(data_required).replace("'","&#39;"),
                   'data_scoring': json.dumps(data_scoring).replace("'","&#39;"),
                   'data_selected_majors': json.dumps(data_selected_majors).replace("'","&#39;"),

                   'faculty_interview_date': faculty_interview_date,
                   'additional_interview_condition': admission_criteria.additional_interview_condition,
                   'interview_date': admission_criteria.interview_date,
                   })


def handle_edit_criteria(admission_criteria, faculty, faculty_choices, request, user, project_id, round_id, project):
    if (not project.is_criteria_edit_allowed) and (not user.is_super_admin):
        return HttpResponseForbidden()
    upsert_admission_criteria(
        request.POST, admission_criteria=admission_criteria,
        user=user)
    request.session['notice'] = "แก้ไขเกณฑ์ สำเร็จ"
    faculty_url_query = '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id)
    return redirect_to_project_index_with_query(faculty_url_query, project_id, round_id)


def redirect_to_project_index_with_query(faculty_url_query, project_id, round_id):
    return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]) + faculty_url_query,
                    is_complete=True)


@user_login_required
def delete(request, project_id, round_id, criteria_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_criteria = get_object_or_404(AdmissionCriteria, pk=criteria_id)

    if not can_user_view_project(user, project):
        return redirect_to_project_index(project_id, round_id)

    faculty, faculty_choices = extract_user_faculty(request, user)
    if admission_criteria.admission_project.id != project_id or (
            not user.profile.is_admission_admin and faculty.id != admission_criteria.faculty.id):
        return redirect_to_project_index(project_id, round_id)

    if request.method == 'POST':
        admission_criteria.is_deleted = True
        admission_criteria.save()

        request.session['notice'] = "ลบเกณฑ์ สำเร็จ"

    faculty_url_query = '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id)

    return redirect(reverse('backoffice:criteria:project-index', args=[project_id, round_id]) + faculty_url_query)


@user_login_required
def update_add_limit(request, project_id, round_id, mid):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    curricum_major_admission_criteria = get_object_or_404(CurriculumMajorAdmissionCriteria, pk=mid)
    admission_criteria = curricum_major_admission_criteria.admission_criteria

    if not can_user_view_project(user, project):
        return redirect_to_project_index(project_id, round_id)

    faculty, faculty_choices = extract_user_faculty(request, user)
    if admission_criteria.admission_project.id != project_id or (
            not user.profile.is_admission_admin and faculty.id != admission_criteria.faculty.id):
        return redirect_to_project_index(project_id, round_id)

    if request.method != 'POST':
        return HttpResponseForbidden()

    add_limit = request.POST['value'].strip()

    if ((add_limit in ['A', 'B']) or
            (add_limit.startswith('C') and add_limit[1:].isdigit())):
        curricum_major_admission_criteria.add_limit = add_limit
        curricum_major_admission_criteria.save()
    else:
        return HttpResponseForbidden()

    return HttpResponse(add_limit)


@user_login_required
def update_accepted_curriculum_type(request, project_id, round_id, acid, ctypeid):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    admission_criteria = get_object_or_404(AdmissionCriteria, pk=acid)
    cur_type = int(ctypeid)

    if not can_user_view_project(user, project):
        return redirect_to_project_index(project_id, round_id)

    faculty, faculty_choices = extract_user_faculty(request, user)
    if admission_criteria.admission_project.id != project_id or (
            not user.profile.is_admission_admin and faculty.id != admission_criteria.faculty.id):
        return redirect_to_project_index(project_id, round_id)

    if request.method != 'POST':
        return HttpResponseForbidden()

    admission_criteria.toggle_accepted_curriculum_type(cur_type)
    admission_criteria.save()

    return render(request,
                  'criteria/include/curriculum_type_form.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'admission_criteria': admission_criteria,
                   })


@user_login_required
def update_accepted_graduate_year(request, project_id, round_id, acid, ytypeid):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    admission_criteria = get_object_or_404(AdmissionCriteria, pk=acid)
    year_type = int(ytypeid)

    if not can_user_view_project(user, project):
        return redirect_to_project_index(project_id, round_id)

    faculty, faculty_choices = extract_user_faculty(request, user)
    if admission_criteria.admission_project.id != project_id or (
            not user.profile.is_admission_admin and faculty.id != admission_criteria.faculty.id):
        return redirect_to_project_index(project_id, round_id)

    if request.method != 'POST':
        return HttpResponseForbidden()

    admission_criteria.toggle_accepted_graduate_year(year_type)
    admission_criteria.save()

    return render(request,
                  'criteria/include/graduate_year_form.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'admission_criteria': admission_criteria,
                   })


@user_login_required
def update_faculty_interview_date(request, project_id, round_id, faculty_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    faculty = get_object_or_404(Faculty, pk=faculty_id) 

    if not can_user_view_project(user, project):
        return redirect_to_project_index(project_id, round_id)
    
    user_faculty, faculty_choices = extract_user_faculty(request, user)
    if not user.profile.is_admission_admin and ((user_faculty == None) or (faculty.id != user_faculty.id)):
        return redirect_to_project_index(project_id, round_id)

    if request.method != 'POST':
        return HttpResponseForbidden()

    faculty_interview_date = AdmissionProjectFacultyInterviewDate.get_from(project, faculty)

    custom_interview_date = request.POST.get('custom_interview_date','1')
    if custom_interview_date == '1':
        faculty_interview_date.is_major_specific = True
        faculty_interview_date.interview_date = None
    elif custom_interview_date == '0':
        faculty_interview_date.is_major_specific = False
        faculty_interview_date.interview_date = None
    else:
        from datetime import date
        faculty_interview_date.is_major_specific = False
        faculty_interview_date.interview_date = date.fromisoformat(custom_interview_date)

    faculty_interview_date.save()
        
    faculty_url_query = '' if faculty_choices == [] else '?faculty_id=' + str(faculty.id)

    return redirect_to_project_index_with_query(faculty_url_query, project_id, round_id)

@user_login_required
def select_curriculum_majors(request, project_id, round_id, code_id=0, value='none'):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)

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


from backoffice.views import sort_admission_projects

@user_login_required
def list_curriculum_majors(request):
    user = request.user

    admission_rounds = AdmissionRound.objects.all()

    faculty, faculty_choices = extract_user_faculty(request, user)
    major_choices = MajorCuptCode.objects.filter(faculty=faculty)
    curriculum_majors = CurriculumMajor.objects.filter(faculty=faculty).all()
    if not user.profile.is_admission_admin:
        admission_projects = user.profile.admission_projects.filter(
            is_visible_in_backoffice=True).all()
    else:
        admission_projects = AdmissionProject.objects.filter(is_visible_in_backoffice=True)

    admission_projects = sort_admission_projects(admission_projects)

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


@user_login_required
def report_num_slots(request, round_id):
    user = request.user
    if not user.profile.is_admission_admin:
        return HttpResponseForbidden()

    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    admission_rounds = AdmissionRound.objects.all()

    faculties = Faculty.objects.order_by('campus_id', 'id').all()
    admission_projects = [p for p in
                          AdmissionProject.objects.filter(is_visible_in_backoffice=True)
                          if admission_round in p.admission_rounds.all()]

    pmap = {p.id: r for p, r in zip(admission_projects, range(len(admission_projects)))}
    fmap = {f.id: r for f, r in zip(faculties, range(len(faculties)))}

    slots = []
    for f in faculties:
        slots.append([0] * len(admission_projects))

    cmap = {}
    for c in AdmissionCriteria.objects.filter(is_deleted=False):
        if c.admission_project_id in pmap:
            cmap[c.id] = (fmap[c.faculty_id], pmap[c.admission_project_id])

    for major_criteria in CurriculumMajorAdmissionCriteria.objects.all():
        if major_criteria.admission_criteria_id in cmap:
            f, p = cmap[major_criteria.admission_criteria_id]
            slots[f][p] += major_criteria.slots

    return render(request,
                  'criteria/report_num_slots.html',
                  {'admission_round': admission_round,
                   'admission_rounds': admission_rounds,
                   'faculties': faculties,
                   'admission_projects': admission_projects,
                   'faculty_slots': zip(faculties, slots),
                   })
