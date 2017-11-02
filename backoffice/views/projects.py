import json

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionRound
from appl.models import ProjectApplication, Payment, Major
from appl.models import ProjectUploadedDocument, UploadedDocument

from backoffice.views.permissions import can_user_view_project, can_user_view_applicant_in_major
from backoffice.decorators import user_login_required

from backoffice.models import CheckMarkGroup, JudgeComment

def load_applicant_round_paid_amount(admission_round):
    round_payments = Payment.objects.select_related('applicant').filter(admission_round=admission_round)

    paid_amount = {}
    for p in round_payments:
        if p.applicant:
            if p.applicant.national_id not in paid_amount:
                paid_amount[p.applicant.national_id] = 0
            paid_amount[p.applicant.national_id] += p.amount

    return paid_amount
        
def filter_faculty_applicants(applicants, faculty):
    faculty_applicants = []
    for a in applicants:
        if len(a.majors)==0:
            continue
        found = False
        for m in a.majors:
            if m.faculty_id == faculty.id:
                found = True
                break
        if found:
            faculty_applicants.append(a)
    return faculty_applicants


def load_project_applicants(project, admission_round, faculty):
    applicant_paid_amount = load_applicant_round_paid_amount(admission_round)
    project_applications = ProjectApplication.find_for_project_and_round(project,
                                                                         admission_round,
                                                                         True)
    major_map = project.get_majors_as_dict()
    applicants = []

    for app in project_applications:
        applicant = app.applicant

        try:
            major_selection = app.major_selection
            applicant.major_selection = major_selection
            applicant.majors = []
            for num in major_selection.get_major_numbers():
                applicant.majors.append(major_map[num])
            if project.max_num_selections == 1:
                if len(applicant.majors)!=0:
                    applicant.major_number = applicant.majors[0].number
                else:
                    applicant.major_number = 1000000000
        except:
            applicant.major_selection = None
            applicant.majors = []
            applicant.major_number = 1000000000

        admission_fee = app.admission_fee(project_base_fee=project.base_fee,
                                          majors=applicant.majors)
        applicant.has_paid = applicant_paid_amount.get(applicant.national_id,0) >= admission_fee
            
        applicants.append(applicant)
        
    if faculty:
        applicants = filter_faculty_applicants(applicants, faculty)
        
    return applicants


def process_applicant_stats(majors, applicants, max_num_selections):
    mnum_map = {}
    midx = 0
    for m in majors:
        mnum_map[m.number] = midx
        m.stats = []
        for i in range(max_num_selections):
            m.stats.append({'sel': 0, 'paid': 0})
        midx += 1

    faculty_stats = {}
        
    for a in applicants:
        r = 0
        for m in a.majors:
            if m.number in mnum_map:
                majors[mnum_map[m.number]].stats[r]['sel'] += 1
                if a.has_paid:
                    majors[mnum_map[m.number]].stats[r]['paid'] += 1

                if max_num_selections == 1:
                    if m.faculty_id not in faculty_stats:
                        faculty_stats[m.faculty_id] = {'sel': 0, 'paid': 0}
                    faculty_stats[m.faculty_id]['sel'] += 1
                    if a.has_paid:
                        faculty_stats[m.faculty_id]['paid'] += 1

                    majors[mnum_map[m.number]].faculty_stat = faculty_stats[m.faculty_id]
            r += 1
    return majors


def load_major_applicant_with_major_stats(project, admission_round, major, num):
    project_applications = ProjectApplication.find_for_project_and_round(project,
                                                                         admission_round,
                                                                         True)
    applicant_paid_amount = load_applicant_round_paid_amount(admission_round)
    major_map = project.get_majors_as_dict()
    
    applicants = []
    for application in project_applications:
        if not hasattr(application, 'major_selection'):
            continue
        major_numbers = application.major_selection.get_major_numbers()

        applicant = application.applicant

        if major in major_numbers:
            admission_fee = application.admission_fee(project_base_fee=project.base_fee,
                                                      majors=application.major_selection.get_majors(major_map))
            applicant.has_paid = applicant_paid_amount.get(applicant.national_id,0) >= admission_fee
            
            applicants.append(applicant)
            
    amaps = dict([(a.id,a) for a in applicants])
    sorted_applicant_ids = [x[2] for x in sorted([(({True: 0, False: 1}[applicant.has_paid]),
                                                   applicant.national_id,
                                                   applicant.id) for applicant
                                                  in applicants])]
    sorted_applicants = [amaps[i] for i in sorted_applicant_ids]

    stat = {'total': len(sorted_applicants),
            'paid': len([a for a in sorted_applicants if a.has_paid]),}
    
    if len(sorted_applicants) > num:
        return sorted_applicants[num], stat
    else:
        return None, stat


@user_login_required
def index(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)
    
    if not can_user_view_project(user, project):
        return redirect(reverse('backoffice:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
    else:
        faculty = None

    majors = project.major_set.all()

    if faculty:
        majors = [m for m in majors if m.faculty_id == faculty.id]

    project_max_num_selections = project.max_num_selections
    applicants = load_project_applicants(project, admission_round, faculty)

    process_applicant_stats(majors, applicants, project_max_num_selections)
    ranks = range(1, project_max_num_selections+1)

    applicant_info_viewable = project_round.applicant_info_viewable
    
    return render(request,
                  'backoffice/projects/index.html',
                  { 'project': project,
                    'admission_round': admission_round,
                    'faculty': faculty,
                    'majors': majors,

                    'applicant_count': len(applicants),
                    'paid_applicant_count': len([a for a in applicants if a.has_paid]),
                    'ranks': ranks,

                    'applicant_info_viewable': applicant_info_viewable,
                  })


@user_login_required
def list_applicants(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    if not can_user_view_project(user, project):
        return redirect(reverse('backoffice:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
    else:
        faculty = None
    
    applicants = load_project_applicants(project, admission_round, faculty)
        
    if project.max_num_selections==1:
        amap = dict([(a.id,a) for a in applicants])
        sorted_applicants = [x[3] for x in sorted([(applicant.major_number,
                                                    ({True: 0, False: 1}[applicant.has_paid]),
                                                    applicant.national_id,
                                                    applicant.id) for applicant
                                                   in applicants])]
        applicants = [amap[i] for i in sorted_applicants]

        sorted_by_majors = True
    else:
        sorted_by_majors = False
        
    return render(request,
                  'backoffice/projects/list_applicants.html',
                  { 'project': project,
                    'faculty': faculty,
                    'admission_round': admission_round,
                    'applicants': applicants,
                    'sorted_by_majors': sorted_by_majors,
                  })


@user_login_required
def show_applicant(request, project_id, round_id, major_number, rank):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    major = Major.get_by_project_number(project, major_number)

    real_rank = int(rank) - 1
    if real_rank < 0:
        return redirect(reverse('backoffice:projects-show-applicant',args=[project_id, round_id, major_number, 1]))
    
    major_number = int(major_number)

    applicant, major_stat = load_major_applicant_with_major_stats(project, admission_round, major_number, real_rank)

    if not applicant:
        return redirect(reverse('backoffice:projects-show-applicant',args=[project_id, round_id, major_number, 1]))

    application = applicant.get_active_application(admission_round)

    if application.admission_project_id != project.id:
        return HttpResponseNotFound()

    if not can_user_view_applicant_in_major(user, applicant, application, project, major):
        return redirect(reverse('backoffice:index'))

    uploaded_documents = (list(ProjectUploadedDocument.get_common_documents()) + 
                          list(project.projectuploadeddocument_set.all()))

    for doc in uploaded_documents:
        doc.applicant_uploaded_documents = doc.get_uploaded_documents_for_applicant(applicant)

    if hasattr(applicant,'educationalprofile'):
        education = applicant.educationalprofile
    else:
        education = None
        
    if hasattr(application,'check_mark_group'):
        check_mark_group = application.check_mark_group
    else:
        check_mark_group = CheckMarkGroup(applicant=applicant,
                                          project_application=application)
        check_mark_group.save()

    judge_comments = application.judge_comment_set.all()
        
    return render(request,
                  'backoffice/projects/show_applicant.html',
                  { 'project': project,
                    'admission_round': admission_round,
                    'major': major,
                    
                    'applicant': applicant,
                    'application': application,
                    'has_paid': application.has_paid(),
                    'rank': rank,

                    'major_stat': major_stat,
                    'rank_choices': range(1,major_stat['total']+1),

                    'uploaded_documents': uploaded_documents,
                    'education': education,

                    'check_mark_group': check_mark_group,
                    'judge_comments': judge_comments,
                  })


@user_login_required
def download_applicant_document(request, project_id, round_id, major_number,
                                national_id, project_uploaded_document_id, document_id):

    from appl.views.upload import get_uploaded_document_or_403
    from appl.views.upload import download_uploaded_document_response
    
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    major = Major.get_by_project_number(project, major_number)
    
    applicant = get_object_or_404(Applicant, national_id=national_id)
    application = applicant.get_active_application(admission_round)

    if application.admission_project_id != project.id:
        return HttpResponseNotFound()

    if not can_user_view_applicant_in_major(user, applicant, application, project, major):
        return redirect(reverse('backoffice:index'))
    
    project_uploaded_document = get_object_or_404(ProjectUploadedDocument,pk=project_uploaded_document_id)
    uploaded_document = get_object_or_404(UploadedDocument,pk=document_id)

    if uploaded_document.applicant_id != applicant.id:
        return HttpResponseForbidden()

    return download_uploaded_document_response(uploaded_document)


@user_login_required
def check_mark_toggle(request, project_id, round_id, national_id, major_number, number):
    user = request.user
    applicant = get_object_or_404(Applicant, national_id=national_id)
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    major = Major.get_by_project_number(project, major_number)

    application = applicant.get_active_application(admission_round)

    if application.admission_project_id != project.id:
        return HttpResponseNotFound()

    if not can_user_view_applicant_in_major(user, applicant, application, project, major):
        return redirect(reverse('backoffice:index'))

    if hasattr(application,'check_mark_group'):
        check_mark_group = application.check_mark_group
    else:
        check_mark_group = CheckMarkGroup(applicant=applicant,
                                          project_application=application)
        check_mark_group.save()

    if check_mark_group.check_marks == '':
        check_mark_group.init_marks()

    number = int(number)
    if check_mark_group.is_checked(number):
        check_mark_group.set_uncheck(number)
    else:
        check_mark_group.set_check(number)
    check_mark_group.save()

    LogItem.create('Toggle mark ({0}) by {1}'.format(number, user.username),
                   applicant,
                   request)
    
    from django.template import loader
    template = loader.get_template('backoffice/projects/include/check_mark_group.html')

    html = template.render({ 'check_mark_group': check_mark_group }, request)
    
    return HttpResponse(json.dumps({ 'result': 'OK',
                                     'html': html }),
                        content_type='application/json')


@user_login_required
def save_comment(request, project_id, round_id, national_id, major_number):
    user = request.user
    applicant = get_object_or_404(Applicant, national_id=national_id)
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    major = Major.get_by_project_number(project, major_number)

    application = applicant.get_active_application(admission_round)

    if application.admission_project_id != project.id:
        return HttpResponseNotFound()

    if not can_user_view_applicant_in_major(user, applicant, application, project, major):
        return redirect(reverse('backoffice:index'))

    comment = JudgeComment(applicant=applicant,
                           project_application=application,
                           body=request.POST.get('body',''),
                           author_username=user.username)
    if comment.body.strip() != '':
        comment.save()

        LogItem.create('Added comment by ' + user.username,
                       applicant,
                       request)
    
        from django.template import loader
        template = loader.get_template('backoffice/projects/include/judge_comment_list.html')

        judge_comments = application.judge_comment_set.all()
        html = template.render({ 'judge_comments': judge_comments }, request)
    
        return HttpResponse(json.dumps({ 'result': 'OK',
                                         'html': html }),
                            content_type='application/json')
    else:
        return HttpResponse(json.dumps({ 'result': 'ERROR', }),
                            content_type='application/json')

                           
