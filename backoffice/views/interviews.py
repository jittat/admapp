from django.shortcuts import render, get_object_or_404

from appl.models import Faculty, AdmissionProject, AdmissionRound
from backoffice.decorators import user_login_required
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
            is_visible_in_backoffice=True).all()
    else:
        admission_projects = AdmissionProject.objects.filter(is_visible_in_backoffice=True)

    for p in admission_projects:
        p.adm_rounds = set([r.id for r in p.admission_rounds.all()])

    major_table = []

    round_table = []
    for m in majors:
        row = []
        for p in admission_projects:
            if admission_round.id in p.adm_rounds:
                row.append(False)
        round_table.append(row)

    c = 0
    for p in admission_projects:
        if admission_round.id in p.adm_rounds:
            cmajor_set = set([cm.cupt_code_id for cm in curriculum_majors
                              if cm.admission_project_id == p.id])
            for m, i in zip(majors, range(len(majors))):
                round_table[i][c] = m.id in cmajor_set

            c += 1

    major_table.extend(list(zip(majors, round_table)))

    return render(request,
                  'backoffice/interviews/description.html',
                  { 'admission_round': admission_round,
                    'admission_projects': admission_projects,
                    'majors': majors,
                    'faculty': faculty,
                    'round_major_table': major_table})
