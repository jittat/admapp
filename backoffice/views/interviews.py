import random

from django.shortcuts import render, get_object_or_404, redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.urls import reverse


from appl.models import Faculty, AdmissionProject, AdmissionRound
from backoffice.decorators import user_login_required
from backoffice.forms.interview_form import InterviewDescriptionForm
from backoffice.models import (
    InterviewDescription,
    AdmissionProjectMajorCuptCodeInterviewDescription,
)
from criteria.models import MajorCuptCode, CurriculumMajor


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
                    (project_majors_id, major.title + "_" + str(admission_project.id))
                )
            round_table[i][j] = {
                "id": project_majors_id,
                "is_disabled": is_disabled,
                "is_checked": is_project_major_selected_by_current_form,
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
            form = InterviewDescriptionForm(instance=interview_description)
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


def handle_file(request, name):
    try:
        interview_img = request.FILES[name]
        # do something with the uploaded file
    except MultiValueDictKeyError:
        # no file was uploaded
        pass
    except Exception as e:
        # handle other errors
        print("Error uploading file:", e)
