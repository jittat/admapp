from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import Http404, HttpResponse
from django.contrib import messages

from appl.models import Faculty, AdmissionProject, AdmissionRound, Major
from backoffice.decorators import user_login_required
from backoffice.forms.interview_form import InterviewDescriptionForm
from backoffice.models import (
    InterviewDescription,
    AdmissionProjectMajorCuptCodeInterviewDescription,
)
from criteria.models import MajorCuptCode, CurriculumMajor


def get_project_major_cupt_code_id(major_cupt_code_id, project_id):
    return str(major_cupt_code_id) + "_" + str(project_id)


def get_preselect_project_major(request):
    if request.method == "POST":
        return None
    project_id = request.GET.get("project_id")
    major_cupt_code_id = request.GET.get("major_cupt_code_id")
    return get_project_major_cupt_code_id(major_cupt_code_id, project_id)


def get_major_cupt_code_id(program_code):
    codes = MajorCuptCode.objects.filter(program_code=program_code)
    if len(codes) != 0:
        return codes[0].id
    else:
        return 0


@user_login_required
def interview_image(request, admission_round_id, faculty_id, description_id, type):
    interview_description = get_object_or_404(InterviewDescription, pk=description_id)

    if type == "description":
        file_model = interview_description.description_image
    elif type == "preparation":
        file_model = interview_description.preparation_image
    else:
        raise Http404()

    try:
        with file_model.open("rb") as file:
            return HttpResponse(file, content_type="image/png")
    except ValueError:
        raise Http404()


@user_login_required
def interview_form(request, admission_round_id, faculty_id, description_id=None):
    preselect_project_major = get_preselect_project_major(request)
    interview_description = None
    if description_id is not None:
        interview_description = get_object_or_404(InterviewDescription, pk=description_id)

    major_id = request.GET.get("major_id", None)
    major = None
    if interview_description:
        major = interview_description.major
    if major_id:
        major = Major.objects.get(pk=major_id)
    if major:
        current_admission_project = major.admission_project
        if preselect_project_major == get_project_major_cupt_code_id(None, None):
            preselect_project_major = get_project_major_cupt_code_id(
                get_major_cupt_code_id(major.cupt_full_code),
                major.admission_project_id)
    else:
        current_admission_project = None

    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)
    faculty = get_object_or_404(Faculty, pk=faculty_id)

    user = request.user

    major_cupt_codes = MajorCuptCode.objects.filter(faculty=faculty_id)
    curriculum_majors = CurriculumMajor.objects.filter(faculty=faculty).all()

    if not user.profile.is_admission_admin:
        admission_projects = user.profile.admission_projects.filter(
            is_visible_in_backoffice=True
        ).all()
    else:
        admission_projects = AdmissionProject.objects.filter(is_visible_in_backoffice=True)

    for admission_project in admission_projects:
        admission_project.adm_rounds = set([r.id for r in admission_project.admission_rounds.all()])

    selected_admission_project_major_cupt_code_list = (
        AdmissionProjectMajorCuptCodeInterviewDescription.objects.filter(
            admission_project__admission_rounds=admission_round_id,
            major_cupt_code__faculty=faculty_id,
        )
    )

    map_selected_admission_project_major_cupt_code = dict()

    for (
            selected_admission_project_major_cupt_code
    ) in selected_admission_project_major_cupt_code_list:
        considered_obj_admission_project_id = (
            selected_admission_project_major_cupt_code.admission_project.id
        )
        considered_obj_major_cupt_code_id = (
            selected_admission_project_major_cupt_code.major_cupt_code.id
        )
        map_selected_admission_project_major_cupt_code[
            (considered_obj_major_cupt_code_id, considered_obj_admission_project_id)
        ] = selected_admission_project_major_cupt_code.interview_description.id

    current_round_project_list = [
        admission_project
        for admission_project in admission_projects
        if admission_round.id in admission_project.adm_rounds
    ]

    major_table = []

    round_table = []
    project_majors_choices = []
    for major_cupt_code in major_cupt_codes:
        row = []
        for admission_project in current_round_project_list:
            row.append(False)
        round_table.append(row)

    j = 0
    for admission_project in current_round_project_list:
        cmajor_set = set(
            [
                cm.cupt_code_id
                for cm in curriculum_majors
                if cm.admission_project_id == admission_project.id
            ]
        )
        for i, major_cupt_code in enumerate(major_cupt_codes):
            is_project_major_has_interview_description = (
                                                             major_cupt_code.id,
                                                             admission_project.id,
                                                         ) in map_selected_admission_project_major_cupt_code

            project_majors_id = get_project_major_cupt_code_id(major_cupt_code.id, admission_project.id)
            is_project_major_preselect = project_majors_id == preselect_project_major
            is_project_major_selected_by_current_form = (
                    is_project_major_has_interview_description
                    and map_selected_admission_project_major_cupt_code[
                        (major_cupt_code.id, admission_project.id)] == description_id
            )

            is_disabled = (
                    is_project_major_has_interview_description
                    and not is_project_major_selected_by_current_form
            )

            if not is_disabled:
                project_majors_choices.append(
                    (project_majors_id, str(major_cupt_code.id) + "_" + str(admission_project))
                )
            round_table[i][j] = {
                "id": project_majors_id,
                "is_disabled": is_disabled,
                "is_checked": is_project_major_selected_by_current_form
                              or is_project_major_preselect,
                "admission_project_name": admission_project,
                "admission_project_id": admission_project.pk,
                "major_title": str(major_cupt_code),
                "major_id": major_cupt_code.id,
                "url": "url-to-related-interview",
            }

        j += 1

    major_table.extend(list(zip(major_cupt_codes, round_table)))

    project_choices = [("None", "ไม่ระบุ")] + [
        (str(admission_project.id), admission_project.title)
        for admission_project in admission_projects
    ]

    major_choices = [("", "ไม่ระบุ")] + [(str(major_cupt_code.id), major_cupt_code.__str__()) for major_cupt_code in
                                         major_cupt_codes]

    if request.method == "POST":
        form = InterviewDescriptionForm(request.POST, request.FILES, instance=interview_description)

        form.admission_round_id = admission_round_id
        form.faculty_id = faculty_id
        form.fields["project_majors"].choices = project_majors_choices
        # form.fields["selected_project"].choices = project_choices
        # form.fields["selected_major"].choices = major_choices
        if form.is_valid():
            if not interview_description:
                interview_description = form.save()
                this_major = Major.objects.get(pk=major_id)
                interview_description.major = this_major
                interview_description.admission_project = this_major.admission_project
                interview_description.save()
            else:
                interview_description = form.save()
            messages.success(request, 'บันทึกข้อมูลสำเร็จ!')
            return redirect(
                reverse(
                    "backoffice:interviews-edit",
                    kwargs={
                        "admission_round_id": admission_round_id,
                        "faculty_id": faculty_id,
                        "description_id": interview_description.id,
                    },
                ),
            )

        else:
            # print the errors to the console
            print(form.errors)
    else:
        if description_id is not None:
            form = InterviewDescriptionForm(instance=interview_description)
        else:
            from datetime import datetime
            form = InterviewDescriptionForm(initial={'interview_date': datetime.fromisoformat('2023-04-26T08:30:00')})
        form.fields["project_majors"].choices = project_majors_choices
        # form.fields["selected_project"].choices = project_choices
        # form.fields["selected_major"].choices = major_choices

    return render(
        request,
        "backoffice/interviews/description.html",
        {
            "interview_description_id": description_id,
            "admission_round": admission_round,
            "admission_projects": current_round_project_list,
            "majors": major_cupt_codes,
            "faculty": faculty,
            "round_major_table": major_table,

            "current_major": major,
            "current_admission_project": current_admission_project,

            "form": form,
        },
    )


@user_login_required
def delete(request, description_id):
    interview_description = get_object_or_404(InterviewDescription, pk=description_id)
    current_admission_project = interview_description.major.admission_project
    admission_round_id = interview_description.admission_round_id

    interview_description.delete()
    messages.info(request, 'ลบข้อมูลรายละเอียดเรียบร้อยแล้ว')
    
    return redirect(reverse('backoffice:projects-index', args=[current_admission_project.id, admission_round_id]))


@user_login_required
def interview_description_list(request, admission_round_id, faculty_id):
    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)
    faculty = get_object_or_404(Faculty, pk=faculty_id)

    interview_descriptions = InterviewDescription.objects.filter(
        admission_round_id=admission_round_id, faculty_id=faculty_id
    )

    major_project_map = dict()
    interview_description_data = list()

    for description in interview_descriptions:
        selected_project_major_objs = (
            AdmissionProjectMajorCuptCodeInterviewDescription.objects.filter(
                description_id=description.pk
            )
        )

        for obj in selected_project_major_objs:
            project_majr_key = f"{obj.major_cupt_code.pk}_{obj.admission_project.pk}"

            major_project_map[project_majr_key] = description.pk

        selected_project_major_data_list = [
            {
                "admission_project_id": obj.admission_project.pk,
                "major_cupt_code_id": obj.major_cupt_code.pk,
                "admission_project_titles": [obj.admission_project.title],
                "majors": [obj.major_cupt_code.display_title()],
            }
            for obj in selected_project_major_objs
        ]

        description_data = {
            "description_id": description.pk,
            "selected_project_major": selected_project_major_data_list,
        }

        interview_description_data.append(description_data)

    user = request.user
    majors = MajorCuptCode.objects.filter(faculty=faculty_id)

    if not user.profile.is_admission_admin:
        admission_projects = user.profile.admission_projects.filter(
            is_visible_in_backoffice=True
        ).all()
    else:
        admission_projects = AdmissionProject.objects.filter(is_visible_in_backoffice=True)

    for admission_project in admission_projects:
        admission_project.adm_rounds = set([r.id for r in admission_project.admission_rounds.all()])

    current_round_project_list = [
        admission_project
        for admission_project in admission_projects
        if admission_round.id in admission_project.adm_rounds
    ]

    major_table = []
    round_table = []
    for major in majors:
        row = []
        for admission_project in current_round_project_list:
            row.append(False)
        round_table.append(row)

    for j, admission_project in enumerate(current_round_project_list):
        for i, major in enumerate(majors):
            project_majors_id = f"{major.id}_{admission_project.id}"

            selected_description = major_project_map.get(project_majors_id, None)

            round_table[i][j] = {
                "admission_project_id": admission_project.id,
                "major_id": major.id,
                "project_majors_id": project_majors_id,
                "interview_description_id": selected_description,
            }

    major_table.extend(list(zip(majors, round_table)))

    return render(
        request,
        "backoffice/interviews/description.html",
        {
            "admission_round": admission_round,
            "admission_projects": current_round_project_list,
            "majors": majors,
            "faculty": faculty,
            "round_major_table": major_table,
            "interview_description_data": interview_description_data,
            "major_project_map": major_project_map,
        },
    )
