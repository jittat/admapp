# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponseServerError

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionRound, Major, MajorSelection, Faculty

from regis.decorators import appl_login_required

# def get_all_majors(request):
#     return 

def process_selection_form(request,
                           applicant,
                           application,
                           major_selection):
    if 'major' not in request.POST:
        return (True, 'คุณยังไม่ได้เลือกสาขา')

    numbers = request.POST.getlist('major')
    majors = []
    for number in numbers:
        major = Major.get_by_project_number(application.admission_project,
                                            number)
        if not major:
            return (True, 'สาขาที่คุณเลือกผิดพลาด')
        majors.append(major)

    major_selection.set_majors(majors)
    major_selection.applicant = applicant
    major_selection.project_application = application
    major_selection.admission_project = application.admission_project
    major_selection.admission_round = application.admission_round
    major_selection.save()

    return (False, '')

@appl_login_required
def select(request, admission_round_id):
    applicant = request.applicant
    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)

    if not admission_round.is_available:
        return HttpResponseForbidden()

    application = applicant.get_active_application(admission_round)
    if not application:
        return HttpResponseForbidden()

    project = application.admission_project
    project_round = project.get_project_round_for(admission_round)
    if not project_round.is_open():
        return redirect(reverse('appl:index'))
    
    try:
        major_selection = application.major_selection
    except MajorSelection.DoesNotExist:
        major_selection = MajorSelection(major_list='')

    error_message = ''

    major = None
    if request.method == 'POST':
        if 'cancel' in request.POST:
            return redirect(reverse('appl:index'))

        if not request.POST.get('major'):
            return redirect(reverse('appl:index'))

        error, error_message = process_selection_form(request,
                                                      applicant,
                                                      application,
                                                      major_selection)
        if not error:
            LogItem.create('Major selection (%s)' % major_selection.major_list,
                           applicant,
                           request)

            return redirect(reverse('appl:index'))

    else:
        selected_majors = major_selection.get_majors()
    

    majors = project.major_set.all()
    majors_dic = dict([(m.faculty_id, True) for m in majors])
    faculties = [f for f in Faculty.objects.all()
                  if f.id in majors_dic]
    
    if project.max_num_selections > 1:
        template = 'appl/major_multiple_selection.html'
    else:
        template = 'appl/major_selection.html'
        if len(selected_majors) == 1:
            selected_majors = selected_majors[0]

    return render(request,
                  template,
                  { 'applicant': applicant,
                    'admission_project': project,
                    'admission_round': admission_round,
                    'application': application,
                    'selected_majors': selected_majors,
                    'faculties': faculties,
                    'all_majors': majors,
                    'error_message': error_message })
    
