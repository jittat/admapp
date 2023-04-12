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
from backoffice.views.permissions import can_user_view_applicants_in_major
from criteria.models import MajorCuptCode


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
    major_id = request.GET.get("major_id", None)

    if major_id is not None:
        checked_interview_description = InterviewDescription.objects.filter(
            major_id=major_id, admission_round_id=admission_round_id, faculty_id=faculty_id
        ).first()
        if checked_interview_description is not None:
            return redirect(
                reverse(
                    "backoffice:interviews-edit",
                    kwargs={
                        "admission_round_id": admission_round_id,
                        "faculty_id": faculty_id,
                        "description_id": checked_interview_description.id,
                    },
                ),
            )

    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)
    faculty = get_object_or_404(Faculty, pk=faculty_id)

    interview_description = get_interview_description(description_id)
    major = get_major(interview_description, major_id)
    preselect_project_major = get_preselect_project_major(request, major)
    current_admission_project = get_current_admission_project(major)
    user = request.user

    if major and (not can_user_view_applicants_in_major(user, major.admission_project, major)):
        return redirect(reverse('backoffice:index'))

    major_cupt_codes = MajorCuptCode.objects.filter(faculty=faculty_id)
    current_round_project_list = get_current_round_project_list(admission_round, user)
    map_selected_admission_project_major_cupt_code = get_map_selected_admission_project_major_cupt_code(
        admission_round_id, faculty_id)

    project_choices = get_project_choices(current_round_project_list)
    major_choices = get_major_choices(major_cupt_codes)
    project_majors_choices, project_majors_data, selected_project_majors = calculate_project_majors(
        current_round_project_list, description_id, major_cupt_codes, map_selected_admission_project_major_cupt_code,
        preselect_project_major)

    if request.method == "POST":
        form = InterviewDescriptionForm(request.POST, request.FILES, instance=interview_description)

        form.admission_round_id = admission_round_id
        form.faculty_id = faculty_id
        form.fields["project_majors"].choices = project_majors_choices

        if form.is_valid():
            if not interview_description:
                interview_description = form.save()
                this_major = Major.objects.get(pk=major_id)
                interview_description.major = this_major
                interview_description.admission_project = this_major.admission_project
                interview_description.save()
            else:
                interview_description = form.save()
            messages.success(request, "บันทึกข้อมูลสำเร็จ!")
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
            print(form.errors)
    else:
        if description_id is not None:
            form = InterviewDescriptionForm(instance=interview_description)
        else:
            from datetime import datetime

            form = InterviewDescriptionForm(
                initial={"interview_date": datetime.fromisoformat("2023-04-26T08:30:00")}
            )
        form.fields["project_majors"].choices = project_majors_choices

    return render(
        request,
        "backoffice/interviews/description.html",
        {
            "interview_description_id": description_id,
            "admission_round": admission_round,
            "admission_projects": current_round_project_list,
            "majors": major_cupt_codes,
            "faculty": faculty,
            "current_major": major,
            "current_admission_project": current_admission_project,
            "form": form,
            "project_majors_data": project_majors_data,
            "major_choices": major_choices,
            "project_choices": project_choices,
            "selected_project_majors": selected_project_majors
        },
    )


def get_major_choices(major_cupt_codes):
    return [
        {'id': str(major_cupt_code.id), 'title': str(major_cupt_code)}
        for major_cupt_code in major_cupt_codes
    ]


def get_project_choices(current_round_project_list):
    return [
        {'id': str(admission_project.id), 'title': admission_project.title}
        for admission_project in current_round_project_list
    ]


def calculate_project_majors(current_round_project_list, description_id, major_cupt_codes,
                             map_selected_admission_project_major_cupt_code, preselect_project_major):
    project_majors_data = {}
    project_majors_choices = []
    selected_project_majors = []
    for admission_project in current_round_project_list:
        project_majors_data[admission_project.id] = []
        for i, major_cupt_code in enumerate(major_cupt_codes):
            project_majors_id = get_project_major_cupt_code_id(
                major_cupt_code.id, admission_project.id
            )

            is_disabled = get_is_disabled(admission_project, description_id, major_cupt_code,
                                          map_selected_admission_project_major_cupt_code)
            title = str(admission_project) + ' / ' + str(major_cupt_code)

            if not is_disabled:
                project_majors_choices.append(
                    (project_majors_id, title)
                )
            is_preselected = get_is_preselected(admission_project, major_cupt_code, preselect_project_major)
            is_checked = get_is_checked(admission_project, description_id, is_preselected, major_cupt_code,
                                        map_selected_admission_project_major_cupt_code)
            project_majors_data[admission_project.id].append({
                "id": project_majors_id,
                "title": title,
                "is_disabled": is_disabled,
                "is_checked": is_checked,
                "admission_project_id": admission_project.pk,
                "major_id": major_cupt_code.id,
                "readonly": is_preselected
            })
            if is_checked:
                selected_project_majors.append(
                    {'id': project_majors_id, 'title': title, 'readonly': is_preselected}
                )
    return project_majors_choices, project_majors_data, selected_project_majors


def get_is_preselected(admission_project, major_cupt_code, preselect_project_major):
    return get_project_major_cupt_code_id(major_cupt_code.id, admission_project.id) == preselect_project_major


def get_is_checked(admission_project, description_id, is_preselected, major_cupt_code,
                   map_selected_admission_project_major_cupt_code):
    is_in_this_description = (
                                 major_cupt_code.id,
                                 admission_project.id,) in map_selected_admission_project_major_cupt_code and \
                             map_selected_admission_project_major_cupt_code[
                                 (major_cupt_code.id, admission_project.id)] == description_id
    is_checked = is_in_this_description or is_preselected
    return is_checked


def get_is_disabled(admission_project, description_id, major_cupt_code, map_selected_admission_project_major_cupt_code):
    is_in_other_description = (major_cupt_code.id,
                               admission_project.id,) in map_selected_admission_project_major_cupt_code and not \
                                  map_selected_admission_project_major_cupt_code[
                                      (major_cupt_code.id, admission_project.id)] == description_id
    is_disabled = is_in_other_description
    return is_disabled


def get_project_major_cupt_code_id(major_cupt_code_id, project_id):
    return str(major_cupt_code_id) + "_" + str(project_id)


def get_preselect_project_major(request, major):
    if request.method == "POST":
        return None
    major_cupt_code_id = request.GET.get("major_cupt_code_id") or get_major_cupt_code_id(major.cupt_full_code)
    project_id = request.GET.get("project_id") or major.admission_project_id

    return get_project_major_cupt_code_id(major_cupt_code_id, project_id)


def get_major_cupt_code_id(program_code):
    codes = MajorCuptCode.objects.filter(program_code=program_code)
    if len(codes) != 0:
        return codes[0].id
    else:
        return 0


def get_interview_description(description_id):
    interview_description = None
    if description_id is not None:
        interview_description = get_object_or_404(InterviewDescription, pk=description_id)
    return interview_description


def get_major(interview_description, major_id):
    if major_id:
        return Major.objects.get(pk=major_id)
    if interview_description:
        return interview_description.major
    return None


def get_current_admission_project(major):
    if major:
        return major.admission_project
    return None


def get_default_preselect_project_major(major):
    return get_project_major_cupt_code_id(
        get_major_cupt_code_id(major.cupt_full_code), major.admission_project_id
    )


def get_current_round_project_list(admission_round, user):
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
    return current_round_project_list


def get_map_selected_admission_project_major_cupt_code(admission_round_id, faculty_id):
    map_selected_admission_project_major_cupt_code = dict()
    selected_admission_project_major_cupt_code_list = (
        AdmissionProjectMajorCuptCodeInterviewDescription.objects.filter(
            admission_project__admission_rounds=admission_round_id,
            major_cupt_code__faculty=faculty_id,
        )
    )
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
    return map_selected_admission_project_major_cupt_code


@user_login_required
def delete(request, description_id):
    interview_description = get_object_or_404(InterviewDescription, pk=description_id)
    current_admission_project = interview_description.major.admission_project
    admission_round_id = interview_description.admission_round_id

    interview_description.delete()
    messages.info(request, "ลบข้อมูลรายละเอียดเรียบร้อยแล้ว")

    return redirect(
        reverse(
            "backoffice:projects-index", args=[current_admission_project.id, admission_round_id]
        )
    )
