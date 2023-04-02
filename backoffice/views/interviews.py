from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import Http404, HttpResponse

from appl.models import Faculty, AdmissionProject, AdmissionRound
from backoffice.decorators import user_login_required
from backoffice.forms.interview_form import InterviewDescriptionForm
from backoffice.models import (
    InterviewDescription,
    AdmissionProjectMajorCuptCodeInterviewDescription,
)
from criteria.models import MajorCuptCode, CurriculumMajor


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
    interview_description = None
    if description_id is not None:
        interview_description = get_object_or_404(InterviewDescription, pk=description_id)

    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)
    faculty = get_object_or_404(Faculty, pk=faculty_id)

    user = request.user

    majors = MajorCuptCode.objects.filter(faculty=faculty_id)
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
    for major in majors:
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
        for i, major in enumerate(majors):
            is_project_major_has_interview_description = (
                major.id,
                admission_project.id,
            ) in map_selected_admission_project_major_cupt_code

            is_project_major_selected_by_current_form = (
                is_project_major_has_interview_description
                and map_selected_admission_project_major_cupt_code[(major.id, admission_project.id)]
                == description_id
            )

            is_disabled = (
                is_project_major_has_interview_description
                and not is_project_major_selected_by_current_form
            )

            project_majors_id = str(major.id) + "_" + str(admission_project.id)
            if not is_disabled:
                project_majors_choices.append(
                    (project_majors_id, str(major) + "_" + str(admission_project))
                )
            round_table[i][j] = {
                "id": project_majors_id,
                "is_disabled": is_disabled,
                "is_checked": is_project_major_selected_by_current_form,
                "admission_project_name": admission_project,
                "admission_project_id": admission_project.pk,
                "major_title": major,
                "major_id": major.pk,
                "url": "url-to-related-interview",
            }

        j += 1

    major_table.extend(list(zip(majors, round_table)))

    if request.method == "POST":
        form = InterviewDescriptionForm(request.POST, request.FILES, instance=interview_description)

        form.admission_round_id = admission_round_id
        form.faculty_id = faculty_id
        form.fields["project_majors"].choices = project_majors_choices
        if form.is_valid():
            interview_description = form.save()

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
            form = InterviewDescriptionForm(None, instance=interview_description)
        else:
            form = InterviewDescriptionForm()
        form.fields["project_majors"].choices = project_majors_choices

    return render(
        request,
        "backoffice/interviews/description.html",
        {
            "interview_description_id": description_id,
            "admission_round": admission_round,
            "admission_projects": current_round_project_list,
            "majors": majors,
            "faculty": faculty,
            "round_major_table": major_table,
            "form": form,
        },
    )


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

