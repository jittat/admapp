import json
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
from backoffice.views.permissions import (
    can_user_view_applicants_in_major,
    can_user_edit_interview_description_span_option,
)
from criteria.models import MajorCuptCode


@user_login_required
def interview(request, description_id):
    interview_description = get_object_or_404(InterviewDescription,pk=description_id)
    major_id = request.GET.get("major_id", None)

    if major_id:
        major = get_object_or_404(Major, pk=major_id)
        admission_project = major.admission_project
    else:
        major = None
        admission_project = None

    contacts = []
    try:
        contacts = interview_description.contacts
    except:
        pass
        
    return render(request, "backoffice/interviews/description_view.html", {
        "interview_description": interview_description,
        "major": major,
        "admission_project": admission_project,
        "contacts": contacts,
    })


@user_login_required
def interview_image(request, description_id, type):
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

    span_option_editable = can_user_edit_interview_description_span_option(
        user, major.admission_project, major
    )

    if major and (not can_user_view_applicants_in_major(user, major.admission_project, major)):
        return redirect(reverse("backoffice:index"))

    major_cupt_codes = MajorCuptCode.objects.filter(faculty=faculty_id)
    current_round_projects = admission_round.get_available_projects()

    project_majors = get_faculty_project_majors(faculty, admission_round, current_round_projects)

    map_selected_admission_project_major_cupt_code = (
        get_map_selected_admission_project_major_cupt_code(admission_round_id, faculty_id)
    )
    available_projects = [project_majors[pid]["project"] for pid in project_majors]
    project_choices = get_project_choices(available_projects)
    major_choices = get_major_choices(major_cupt_codes)

    (
        project_majors_choices,
        project_majors_data,
        selected_project_majors,
        major_choices_for_projects,
    ) = calculate_project_majors(
        available_projects,
        description_id,
        major_cupt_codes,
        map_selected_admission_project_major_cupt_code,
        preselect_project_major,
        project_majors,
    )

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
            "admission_projects": current_round_projects,
            "majors": major_cupt_codes,
            "faculty": faculty,
            "current_major": major,
            "current_admission_project": current_admission_project,
            "form": form,
            "project_majors_data": project_majors_data,
            "major_choices": major_choices,
            "project_choices": project_choices,
            "selected_project_majors": selected_project_majors,
            "major_choices_for_projects": major_choices_for_projects,
            "span_option_editable": span_option_editable,
        },
    )


def get_faculty_project_majors(faculty, admission_round, current_round_projects):
    project_map = {p.id: p for p in current_round_projects}
    faculty_majors = Major.objects.filter(faculty=faculty).order_by("admission_project")
    projects = {}
    for m in faculty_majors:
        if m.admission_project_id not in project_map:
            continue

        p = project_map[m.admission_project_id]
        if p.id not in projects:
            projects[p.id] = {"project": p, "majors": []}
        projects[p.id]["majors"].append(m)
    return projects


def get_major_choices(major_cupt_codes):
    return [
        {"id": str(major_cupt_code.id), "title": str(major_cupt_code)}
        for major_cupt_code in major_cupt_codes
    ]


def get_project_choices(current_round_projects):
    return [
        {"id": str(admission_project.id), "title": admission_project.title}
        for admission_project in current_round_projects
    ]


def calculate_project_majors(
        current_round_projects,
        description_id,
        major_cupt_codes,
        map_selected_admission_project_major_cupt_code,
        preselect_project_major,
        project_majors,
):
    project_majors_data = {}
    project_majors_choices = []
    selected_project_majors = []
    major_choices_for_projects = {}

    major_cupt_code_map = {
        major_cupt_code.get_program_major_code_as_str(): major_cupt_code
        for major_cupt_code in major_cupt_codes
    }

    for admission_project in current_round_projects:
        major_choices_for_projects[admission_project.id] = []

        project_majors_data[admission_project.id] = []
        for major in project_majors[admission_project.id]["majors"]:
            major_cupt_code = major_cupt_code_map[major.cupt_full_code]

            project_majors_id = get_project_major_cupt_code_id(
                major_cupt_code.id, admission_project.id
            )

            is_disabled = get_is_disabled(
                admission_project,
                description_id,
                major_cupt_code,
                map_selected_admission_project_major_cupt_code,
            )
            title = str(admission_project) + " / " + str(major_cupt_code)

            if not is_disabled:
                project_majors_choices.append((project_majors_id, title))

            major_choices_for_projects[admission_project.id].append(
                (major_cupt_code.id, str(major_cupt_code))
            )

            is_preselected = get_is_preselected(
                admission_project, major_cupt_code, preselect_project_major
            )
            is_checked = get_is_checked(
                admission_project,
                description_id,
                is_preselected,
                major_cupt_code,
                map_selected_admission_project_major_cupt_code,
            )
            project_majors_data[admission_project.id].append(
                {
                    "id": project_majors_id,
                    "title": title,
                    "is_disabled": is_disabled,
                    "is_checked": is_checked,
                    "admission_project_id": admission_project.pk,
                    "major_id": major_cupt_code.id,
                    "readonly": is_preselected,
                }
            )
            if is_checked:
                selected_project_majors.append(
                    {"id": project_majors_id, "title": title, "readonly": is_preselected}
                )
    return (
        project_majors_choices,
        project_majors_data,
        selected_project_majors,
        major_choices_for_projects,
    )


def get_is_preselected(admission_project, major_cupt_code, preselect_project_major):
    return (
            get_project_major_cupt_code_id(major_cupt_code.id, admission_project.id)
            == preselect_project_major
    )


def get_is_checked(
        admission_project,
        description_id,
        is_preselected,
        major_cupt_code,
        map_selected_admission_project_major_cupt_code,
):
    is_in_this_description = (
            (
                major_cupt_code.id,
                admission_project.id,
            )
            in map_selected_admission_project_major_cupt_code
            and map_selected_admission_project_major_cupt_code[
                (major_cupt_code.id, admission_project.id)
            ]
            == description_id
    )
    is_checked = is_in_this_description or is_preselected
    return is_checked


def get_is_disabled(
        admission_project,
        description_id,
        major_cupt_code,
        map_selected_admission_project_major_cupt_code,
):
    is_in_other_description = (
            (
                major_cupt_code.id,
                admission_project.id,
            )
            in map_selected_admission_project_major_cupt_code
            and not map_selected_admission_project_major_cupt_code[
                        (major_cupt_code.id, admission_project.id)
                    ]
                    == description_id
    )
    is_disabled = is_in_other_description
    return is_disabled


def get_project_major_cupt_code_id(major_cupt_code_id, project_id):
    return str(major_cupt_code_id) + "_" + str(project_id)


def get_preselect_project_major(request, major):
    if request.method == "POST":
        return None
    major_cupt_code_id = request.GET.get("major_cupt_code_id") or get_major_cupt_code_id(
        major.cupt_full_code
    )
    project_id = request.GET.get("project_id") or major.admission_project_id

    return get_project_major_cupt_code_id(major_cupt_code_id, project_id)


def get_major_cupt_code_id(full_code):
    if len(full_code) == 15:
        codes = MajorCuptCode.objects.filter(program_code=full_code)
    else:
        codes = MajorCuptCode.objects.filter(program_code=full_code[:15], major_code=full_code[-1])
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
            selected_admission_project_major_cupt_code.admission_project_id
        )
        considered_obj_major_cupt_code_id = (
            selected_admission_project_major_cupt_code.major_cupt_code_id
        )
        map_selected_admission_project_major_cupt_code[
            (considered_obj_major_cupt_code_id, considered_obj_admission_project_id)
        ] = selected_admission_project_major_cupt_code.interview_description_id
    return map_selected_admission_project_major_cupt_code


@user_login_required
def list_interview_forms(request, admission_round_id, faculty_id):
    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)
    faculty = get_object_or_404(Faculty, pk=faculty_id)

    interview_descriptions = InterviewDescription.objects.filter(
        faculty_id=faculty_id, admission_round_id=admission_round_id
    )
    major_cupt_codes = MajorCuptCode.objects.filter(faculty=faculty_id)
    current_round_projects = admission_round.get_available_projects()

    project_ids = [project.id for project in current_round_projects]
    major_cupt_codes_ids = [cupt_code.id for cupt_code in major_cupt_codes]
    interview_description_relations = (
        AdmissionProjectMajorCuptCodeInterviewDescription.objects.filter(
            major_cupt_codes_id__in=major_cupt_codes_ids, admission_project_id__in=project_ids
        )
    )

    return render(
        request,
        "backoffice/interviews/description.html",
        {
            "admission_round": admission_round,
            "admission_projects": current_round_projects,
            "majors": major_cupt_codes,
            "faculty": faculty,
            "interview_descriptions": interview_descriptions,
            "interview_description_relations": interview_description_relations,
        },
    )


@user_login_required
def delete(request, description_id):
    interview_description = get_object_or_404(InterviewDescription, pk=description_id)
    current_admission_project = interview_description.major.admission_project
    admission_round_id = interview_description.admission_round_id

    major = interview_description.major
    if major and (not can_user_view_applicants_in_major(request.user, major.admission_project, major)):
        return redirect(reverse("backoffice:index"))
    
    interview_description.delete()
    messages.info(request, "ลบข้อมูลรายละเอียดเรียบร้อยแล้ว")

    return redirect(
        reverse(
            "backoffice:projects-index", args=[current_admission_project.id, admission_round_id]
        )
    )
