import csv
import json
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionRound
from appl.models import ProjectApplication, Payment, Major, AdmissionResult, Faculty
from appl.models import ProjectUploadedDocument, UploadedDocument

from backoffice.views.permissions import can_user_view_project, can_user_view_applicant_in_major, can_user_view_applicants_in_major
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
    faculties = dict([(f.id,f) for f in Faculty.objects.all()])

    for num in major_map.keys():
        m = major_map[num]
        if m.faculty_id in faculties:
            m.faculty = faculties[m.faculty_id]

    applicants = []

    for app in project_applications:
        applicant = app.applicant

        try:
            major_selection = app.major_selection
            applicant.major_selection = major_selection
            applicant.majors = []
            for num in major_selection.get_major_numbers():
                applicant.majors.append(major_map[num])
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


def load_major_applicants(project, admission_round, major):
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

        if major.number in major_numbers:
            admission_fee = application.admission_fee(project_base_fee=project.base_fee,
                                                      majors=application.major_selection.get_majors(major_map))
            applicant.has_paid = applicant_paid_amount.get(applicant.national_id,0) >= admission_fee

            applicants.append(applicant)

    amaps = dict([(a.id,a) for a in applicants])
    sorted_applicant_ids = [x[2] for x in sorted([(({True: 0, False: 1}[applicant.has_paid]),
                                                   applicant.national_id,
                                                   applicant.id) for applicant
                                                  in applicants])]
    return [amaps[i] for i in sorted_applicant_ids]


def load_major_applicant_with_major_stats(project, admission_round, major, num):
    sorted_applicants = load_major_applicants(project, admission_round, major)
    stat = {'total': len(sorted_applicants),
            'paid': len([a for a in sorted_applicants if a.has_paid]),}

    if len(sorted_applicants) > num:
        return sorted_applicants[num], stat
    else:
        return None, stat


def load_accepted_applicant_counts(admission_round, admission_project, majors):
    mmap = dict([(majors[i].id,i) for i in range(len(majors))])

    for m in majors:
        m.accepted_for_interview_count = 0

    results = AdmissionResult.objects.filter(admission_round=admission_round,
                                             admission_project=admission_project)
    for r in results:
        if r.is_accepted_for_interview:
            if r.major_id in mmap:
                midx = mmap[r.major_id]
                majors[midx].accepted_for_interview_count += 1


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
        user_major_number = user.profile.major_number
    else:
        faculty = None
        user_major_number = user.profile.ANY_MAJOR

    majors = project.major_set.all()

    if faculty:
        majors = [m for m in majors if m.faculty_id == faculty.id]

    project_max_num_selections = project.max_num_selections
    applicants = load_project_applicants(project, admission_round, faculty)

    process_applicant_stats(majors, applicants, project_max_num_selections)
    ranks = range(1, project_max_num_selections+1)

    applicant_info_viewable = project_round.applicant_info_viewable

    if applicant_info_viewable:
        load_accepted_applicant_counts(admission_round,
                                       project,
                                       majors)

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

                    'user_major_number': user_major_number,
                    'any_major': user.profile.ANY_MAJOR,
                  })


def load_check_marks_and_results(applicants, admission_project, admission_round):
    result_map = {}

    for r in AdmissionResult.objects.filter(admission_project=admission_project,
                                            admission_round=admission_round):
        if r.applicant_id not in result_map:
            result_map[r.applicant_id] = []
        result_map[r.applicant_id].append(r)

    all_check_marks = (CheckMarkGroup
                       .objects
                       .select_related('project_application')
                       .filter(project_application__admission_project=admission_project)
                       .filter(project_application__admission_round=admission_round)
                       .all())

    check_marks = {}
    for c in all_check_marks:
        check_marks[c.applicant_id] = c

    for a in applicants:
        a.admission_results = result_map.get(a.id, None)
        a.check_marks = check_marks.get(a.id, None)


@user_login_required
def list_applicants(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('backoffice:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
        user_major_number = user.profile.major_number
    else:
        faculty = None
        user_major_number = user.profile.ANY_MAJOR

    applicants = load_project_applicants(project, admission_round, faculty)
    if user_major_number != user.profile.ANY_MAJOR:
        applicants = [a for a in applicants if a.major_number == user_major_number]

    amap = dict([(a.id,a) for a in applicants])
    sorted_applicants = [x[3] for x in sorted([(applicant.major_number,
                                                ({True: 0, False: 1}[applicant.has_paid]),
                                                applicant.national_id,
                                                applicant.id) for applicant
                                               in applicants])]
    applicants = [amap[i] for i in sorted_applicants]
    old_num = -1
    r = 0
    for a in applicants:
        if a.major_number != old_num:
            r = 1
            old_num = a.major_number
        else:
            r += 1
        a.r = r

    sorted_by_majors = (project.max_num_selections == 1)

    applicant_info_viewable = project_round.applicant_info_viewable

    info_col_count = 0
    info_template = ''
    info_header_template = ''

    if applicant_info_viewable:
        load_check_marks_and_results(applicants, project, admission_round)

        from supplements.models import PROJECT_APPLICANT_LIST_ADDITIONS

        if project.title in PROJECT_APPLICANT_LIST_ADDITIONS:
            config = PROJECT_APPLICANT_LIST_ADDITIONS[project.title]
            loader = config['loader']
            for app in applicants:
                app.additional_info = loader(app,
                                             project,
                                             admission_round)
            info_template = config['template']
            info_col_count = config['col_count']
            info_header_template = config['header_template']

    return render(request,
                  'backoffice/projects/list_applicants.html',
                  { 'project': project,
                    'faculty': faculty,
                    'admission_round': admission_round,
                    'applicants': applicants,

                    'info_col_count': info_col_count,
                    'info_template': info_template,
                    'info_header_template': info_header_template,

                    'sorted_by_majors': sorted_by_majors,
                    'applicant_info_viewable': applicant_info_viewable,
                  })


def load_all_judge_comments(application,
                            admission_project,
                            admission_round,
                            major):
    shared_comments = JudgeComment.objects.filter(is_shared_in_major=True, 
                                                  is_deleted=False,
                                                  admission_project=admission_project,
                                                  admission_round=admission_round,
                                                  major=major)
    judge_comments = application.judge_comment_set.filter(is_deleted=False,
                                                          is_shared_in_major=False)

    return list(shared_comments) + list(judge_comments)


@user_login_required
def show_applicant(request, project_id, round_id, major_number, rank):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)
    major = Major.get_by_project_number(project, major_number)

    real_rank = int(rank) - 1
    if real_rank < 0:
        return redirect(reverse('backoffice:projects-show-applicant',args=[project_id, round_id, major_number, 1]))

    applicant, major_stat = load_major_applicant_with_major_stats(project, admission_round, major, real_rank)

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
    if hasattr(applicant,'personalprofile'):
        personal = applicant.personalprofile
    else:
        personal = None

    if hasattr(application,'check_mark_group'):
        check_mark_group = application.check_mark_group
    else:
        check_mark_group = CheckMarkGroup(applicant=applicant,
                                          project_application=application)
        check_mark_group.save()

    judge_comments = load_all_judge_comments(application,
                                             project,
                                             admission_round,
                                             major)

    admission_result = AdmissionResult.get_for_application_and_major(application, major)
    if admission_result:
        is_accepted_for_interview = admission_result.is_accepted_for_interview
        is_accepted = admission_result.is_accepted
    else:
        is_accepted_for_interview = None
        is_accepted = False

    major_accepted_for_interview_count = AdmissionResult.accepted_for_interview_count(admission_round,
                                                                                      major)

    major_accepted_count = AdmissionResult.accepted_count(admission_round,
                                                          major)

    frozen_results = { 'interview': project_round.accepted_for_interview_result_frozen,
                       'acceptance': project_round.accepted_result_shown }

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
                    'major_accepted_for_interview_count': major_accepted_for_interview_count,
                    'major_accepted_count': major_accepted_count,

                    'uploaded_documents': uploaded_documents,
                    'education': education,
                    'personal': personal,

                    'is_accepted_for_interview': is_accepted_for_interview,
                    'is_accepted': is_accepted,

                    'frozen_results': frozen_results,

                    'check_mark_group': check_mark_group,
                    'judge_comments': judge_comments,
                  })


def load_applicant_application_and_check_permission(request, project_id, round_id, national_id, major_number):
    user = request.user

    request.project = get_object_or_404(AdmissionProject, pk=project_id)
    request.admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    request.project_round = request.project.get_project_round_for(request.admission_round)
    request.major = Major.get_by_project_number(request.project, major_number)

    request.applicant = get_object_or_404(Applicant, national_id=national_id)
    request.application = request.applicant.get_active_application(request.admission_round)

    if request.application.admission_project_id != request.project.id:
        return (False, HttpResponseNotFound())

    if not can_user_view_applicant_in_major(user, request.applicant, request.application, request.project, request.major):
        return (False, redirect(reverse('backoffice:index')))

    if not request.application.has_applied_to_major(request.major):
        return (False,HttpResponseForbidden())

    return (True, None)


@user_login_required
def download_applicant_document(request, project_id, round_id, major_number,
                                national_id, project_uploaded_document_id, document_id):

    from appl.views.upload import get_uploaded_document_or_403
    from appl.views.upload import download_uploaded_document_response

    can_view, error_response = load_applicant_application_and_check_permission(request,
                                                                               project_id,
                                                                               round_id,
                                                                               national_id,
                                                                               major_number)
    if not can_view:
        return error_response
    
    applicant = request.applicant
    project_uploaded_document = get_object_or_404(ProjectUploadedDocument,pk=project_uploaded_document_id)
    uploaded_document = get_object_or_404(UploadedDocument,pk=document_id)

    if uploaded_document.applicant_id != applicant.id:
        return HttpResponseForbidden()

    return download_uploaded_document_response(uploaded_document)


@user_login_required
def check_mark_toggle(request, project_id, round_id, national_id, major_number, number):
    can_view, error_response = load_applicant_application_and_check_permission(request,
                                                                               project_id,
                                                                               round_id,
                                                                               national_id,
                                                                               major_number)
    if not can_view:
        return error_response

    user = request.user
    applicant = request.applicant
    application = request.application

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
def set_call_for_interview(request, project_id, round_id, national_id, major_number, decision):
    can_view, error_response = load_applicant_application_and_check_permission(request,
                                                                               project_id,
                                                                               round_id,
                                                                               national_id,
                                                                               major_number)
    if not can_view:
        return error_response

    user = request.user
    applicant = request.applicant
    admission_round = request.admission_round
    major = request.major
    application = request.application

    if request.project_round.accepted_for_interview_result_frozen:
        return HttpResponseForbidden()

    admission_result = AdmissionResult.get_for_application_and_major(application, major)
    if not admission_result:
        admission_result = AdmissionResult(applicant=applicant,
                                           application=application,
                                           admission_project=request.project,
                                           admission_round=admission_round,
                                           major=major)

    if decision == 'accepted':
        admission_result.is_accepted_for_interview = True
    else:
        admission_result.is_accepted_for_interview = False

    admission_result.updated_accepted_for_interview_at = datetime.now()
    admission_result.save()

    LogItem.create('Interview decision (major: {0} {1}) by {2}'.format(major_number,
                                                                       decision,
                                                                       user.username),
                   applicant,
                   request)

    is_accepted_for_interview = admission_result.is_accepted_for_interview

    from django.template import loader
    template = loader.get_template('backoffice/projects/include/interview_buttons.html')

    html = template.render({ 'is_accepted_for_interview': is_accepted_for_interview }, request)

    major_accepted_for_interview_count = AdmissionResult.accepted_for_interview_count(admission_round,
                                                                                      major)

    return HttpResponse(json.dumps({ 'result': 'OK',
                                     'html': html,
                                     'count': major_accepted_for_interview_count }),
                        content_type='application/json')


@user_login_required
def set_acceptance(request, project_id, round_id, national_id, major_number, decision):
    can_view, error_response = load_applicant_application_and_check_permission(request,
                                                                               project_id,
                                                                               round_id,
                                                                               national_id,
                                                                               major_number)
    if not can_view:
        return error_response

    user = request.user
    applicant = request.applicant
    admission_round = request.admission_round
    major = request.major
    application = request.application

    if request.project_round.accepted_result_shown:
        return HttpResponseForbidden()
    
    admission_result = AdmissionResult.get_for_application_and_major(application, major)
    if not admission_result:
        return HttpResponseForbidden()

    if decision == 'accepted':
        admission_result.is_accepted = True
    else:
        admission_result.is_accepted = False

    admission_result.updated_accepted_at = datetime.now()
    admission_result.save()

    LogItem.create('Acceptance decision (major: {0} {1}) by {2}'.format(major_number,
                                                                        decision,
                                                                        user.username),
                   applicant,
                   request)

    is_accepted = admission_result.is_accepted

    from django.template import loader
    template = loader.get_template('backoffice/projects/include/acceptance_buttons.html')

    html = template.render({ 'is_accepted': is_accepted }, request)

    major_accepted_count = AdmissionResult.accepted_count(admission_round,
                                                          major)

    return HttpResponse(json.dumps({ 'result': 'OK',
                                     'html': html,
                                     'count': major_accepted_count }),
                        content_type='application/json')


@user_login_required
def save_comment(request, project_id, round_id, national_id, major_number):
    can_view, error_response = load_applicant_application_and_check_permission(request,
                                                                               project_id,
                                                                               round_id,
                                                                               national_id,
                                                                               major_number)
    if not can_view:
        return error_response

    user = request.user
    applicant = request.applicant
    project = request.project
    admission_round = request.admission_round
    major = request.major
    application = request.application

    comment = JudgeComment(applicant=applicant,
                           project_application=application,
                           body=request.POST.get('body',''),
                           author_username=user.username,
                           is_shared_in_major=False,
                           admission_project=project,
                           admission_round=admission_round)

    if int(request.POST['super_comment']):
        comment.is_shared_in_major = True
        comment.major = major

    if comment.body.strip() != '':
        comment.save()

        LogItem.create('Added comment by ' + user.username,
                       applicant,
                       request)

        from django.template import loader
        template = loader.get_template('backoffice/projects/include/judge_comment_list.html')

        judge_comments = load_all_judge_comments(application,
                                                 project,
                                                 admission_round,
                                                 major)
        
        html = template.render({ 'judge_comments': judge_comments,
                                 'project':project,
                                 'admission_round':admission_round,
                                 'applicant':applicant,
                                 'major':major, }, request)

        return HttpResponse(json.dumps({ 'result': 'OK',
                                         'html': html }),
                            content_type='application/json')
    else:
        return HttpResponse(json.dumps({ 'result': 'ERROR', }),
                            content_type='application/json')


@user_login_required
def delete_comment(request, project_id, round_id, national_id, major_number, comment_id):
    can_view, error_response = load_applicant_application_and_check_permission(request,
                                                                               project_id,
                                                                               round_id,
                                                                               national_id,
                                                                               major_number)
    if not can_view:
        return error_response

    user = request.user
    applicant = request.applicant
    project = request.project
    admission_round = request.admission_round
    major = request.major
    application = request.application

    comment = get_object_or_404(JudgeComment, pk=comment_id)
    comment.is_deleted = True
    comment.save()

    LogItem.create('Delete comment ' + comment_id + ' by ' + user.username,
                   applicant,
                   request)

    from django.template import loader
    template = loader.get_template('backoffice/projects/include/judge_comment_list.html')

    judge_comments = load_all_judge_comments(application,
                                             project,
                                             admission_round,
                                             major)

    html = template.render({'judge_comments': judge_comments,
                            'project': project,
                            'admission_round': admission_round,
                            'applicant': applicant,
                            'major': major }, request)
    
    return HttpResponse(json.dumps({ 'result': 'OK',
                                     'html': html }),
                        content_type='application/json')

