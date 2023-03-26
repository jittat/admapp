import random

from django.shortcuts import render, get_object_or_404, redirect
from django.utils.datastructures import MultiValueDictKeyError

from appl.models import Faculty, AdmissionProject, AdmissionRound
from backoffice.decorators import user_login_required
from backoffice.forms.contact_person_form import ContactPersonFormSet
from backoffice.forms.interview_form import InterviewForm
from criteria.models import MajorCuptCode, CurriculumMajor


@user_login_required
def interview_form(request, admission_round_id, faculty_id, description_id):
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
        for major, i in zip(majors, range(len(majors))):
            is_checked = major.id in cmajor_set
            is_disabled = random.choice([True, False]) if not is_checked else False
            project_majors_id = str(major.id) + "_" + str(admission_project.id)
            project_majors_choices.append(
                (project_majors_id, major.title + "_" + str(admission_project.id))
            )
            round_table[i][j] = {
                "id": project_majors_id,
                "is_checked": is_checked,
                "is_disabled": is_disabled,
                "url": "url-to-related-interview",
            }

        j += 1

    major_table.extend(list(zip(majors, round_table)))

    if request.method == "POST":
        form = InterviewForm(request.POST, request.FILES)
        form.fields["project_majors"].choices = project_majors_choices
        contact_person_formset = ContactPersonFormSet(request.POST, prefix="contact_person")
        if form.is_valid() and contact_person_formset.is_valid():
            print(form.cleaned_data)
            # do something with form data, such as save to database
            pass
        else:
            # print the errors to the console
            print(form.errors)
    else:
        form = InterviewForm()
        form.fields["project_majors"].choices = project_majors_choices
        contact_person_formset = ContactPersonFormSet(prefix="contact_person")

    return render(
        request,
        "backoffice/interviews/description.html",
        {
            "admission_round": admission_round,
            "admission_projects": current_round_project_list,
            "majors": majors,
            "faculty": faculty,
            "round_major_table": major_table,
            "form": form,
            "contact_person_formset": contact_person_formset,
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
