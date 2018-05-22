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

from backoffice.models import CheckMarkGroup, JudgeComment, MajorInterviewCallDecision

def load_applicant_round_paid_amount(admission_round):
    round_payments = Payment.objects.filter(admission_round=admission_round)

    paid_amount = {}
    for p in round_payments:
        if p.applicant_id:
            if p.applicant_id not in paid_amount:
                paid_amount[p.applicant_id] = 0
            paid_amount[p.applicant_id] += p.amount

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
        applicant.has_paid = applicant_paid_amount.get(applicant.id,0) >= admission_fee

        applicants.append(applicant)

    if faculty:
        applicants = filter_faculty_applicants(applicants, faculty)

    return applicants


def process_applicant_stats(majors,
                            applicants,
                            max_num_selections,
                            rank_combined=False):
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
            if not rank_combined:
                r += 1
    return majors


def sorted_applicants(applicants, with_interview_call_results=False):
    amaps = dict([(a.id,a) for a in applicants])
    for a in applicants:
        if not hasattr(a,'major_number'):
            a.major_number = 0
    if not with_interview_call_results:
        sorted_applicant_ids = [x[3] for x in sorted([(applicant.major_number,
                                                       ({True: 0, False: 1}[applicant.has_paid]),
                                                       applicant.national_id,
                                                       applicant.id) for applicant
                                                      in applicants])]
    else:
        sorted_applicant_ids = [x[4] for x in sorted([(applicant.major_number,
                                                       ({True: 0, False: 1}[applicant.has_paid]),
                                                       ({True: 0, False: 1}[applicant.is_accepted_for_interview]),
                                                       applicant.national_id,
                                                       applicant.id) for applicant
                                                      in applicants])]
        
    return [amaps[i] for i in sorted_applicant_ids]


def load_major_applicants(project, admission_round, major, with_interview_call_results=False):
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
            applicant.has_paid = applicant_paid_amount.get(applicant.id,0) >= admission_fee

            applicants.append(applicant)

    return sorted_applicants(applicants, with_interview_call_results)


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
        m.criteria_passed_count = 0
        m.accepted_for_interview_count = 0
        m.accepted_count = 0
        m.confirmed_count = 0

    results = AdmissionResult.objects.filter(admission_round=admission_round,
                                             admission_project=admission_project)

    for r in results:
        if r.is_criteria_passed:
            if r.major_id in mmap:
                midx = mmap[r.major_id]
                majors[midx].criteria_passed_count += 1

        if r.is_accepted_for_interview:
            if r.major_id in mmap:
                midx = mmap[r.major_id]
                majors[midx].accepted_for_interview_count += 1

        if r.is_accepted:
            if r.major_id in mmap:
                midx = mmap[r.major_id]
                majors[midx].accepted_count += 1

                if r.has_confirmed:
                    majors[midx].confirmed_count += 1
                    
    decisions = dict([(d.major_id,d) for d in
                      MajorInterviewCallDecision.objects.filter(admission_round=admission_round,
                                                                admission_project=admission_project).all()])
    
    for major_id, decision in decisions.items():
        if major_id in mmap:
            midx = mmap[major_id]
            majors[midx].accepted_for_interview_count = decision.interview_call_count


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

    if not project.has_selections_with_no_ranks:
        project_max_num_selections = project.max_num_selections
    else:
        project_max_num_selections = 1
    applicants = load_project_applicants(project, admission_round, faculty)

    process_applicant_stats(majors,
                            applicants,
                            project_max_num_selections,
                            project.has_selections_with_no_ranks)

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
                    'has_criteria_check': project_round.criteria_check_required,

                    'user_major_number': user_major_number,
                    'any_major': user.profile.ANY_MAJOR,
                  })


def update_applicant_status(applicant, admission_results, admission_project_round):
    applicant.admission_results = admission_results

    applicant.is_accepted = False
    applicant.is_accepted_for_interview = False
    applicant.is_criteria_passed = False
    applicant.is_interview_callable = False
    if applicant.admission_results:
        for res in applicant.admission_results:
            if res.is_accepted:
                applicant.is_accepted = True
                applicant.accepted_result = res
            if (res.is_criteria_passed) or (not admission_project_round.criteria_check_required):
                applicant.is_criteria_passed = True
                if res.is_interview_callable():
                    applicant.is_interview_callable = True
            if res.is_accepted_for_interview:
                applicant.is_accepted_for_interview = True
            applicant.admission_result = res

    if not admission_project_round.criteria_check_required:
        if hasattr(applicant, 'admission_result'):
            applicant.is_criteria_passed = True


def load_check_marks_and_results(applicants,
                                 admission_project,
                                 admission_round,
                                 project_round):
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
        update_applicant_status(a, result_map.get(a.id, None), project_round)
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

    applicant_info_viewable = project_round.applicant_info_viewable

    if applicant_info_viewable:
        load_check_marks_and_results(applicants,
                                     project,
                                     admission_round,
                                     project_round)

    applicants = sorted_applicants(applicants)
    
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

    info_col_count = 0
    info_template = ''
    info_header_template = ''

    if applicant_info_viewable:
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

                    'has_criteria_check': project_round.criteria_check_required,

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

    applicant, major_stat = load_major_applicant_with_major_stats(project,
                                                                  admission_round,
                                                                  major,
                                                                  real_rank)

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
        is_criteria_passed = admission_result.is_criteria_passed
        is_accepted_for_interview = admission_result.is_accepted_for_interview
        is_accepted = admission_result.is_accepted
    else:
        is_criteria_passed = None
        is_accepted_for_interview = None
        is_accepted = False

    if not project_round.criteria_check_required:
        is_criteria_passed = True
        
    major_accepted_for_interview_count = AdmissionResult.accepted_for_interview_count(admission_round,
                                                                                      major)

    major_accepted_count = AdmissionResult.accepted_count(admission_round,
                                                          major)

    frozen_results = {
        'criteria_check_required': project_round.criteria_check_required,
        'criteria': (not project_round.criteria_check_required) or project_round.criteria_check_frozen,
        'interview': project_round.accepted_for_interview_result_frozen,
        'acceptance': project_round.accepted_result_frozen or project_round.accepted_result_shown
    }

    only_bulk_interview_acceptance = project_round.only_bulk_interview_acceptance

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

                    'is_criteria_passed': is_criteria_passed,
                    'is_accepted_for_interview': is_accepted_for_interview,
                    'is_accepted': is_accepted,

                    'frozen_results': frozen_results,

                    'only_bulk_interview_acceptance': only_bulk_interview_acceptance,

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

    if request.project_round.only_bulk_interview_acceptance:
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
    
    if request.project_round.accepted_result_frozen:
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
def set_criteria_result(request, project_id, round_id, national_id, major_number, decision):
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

    if request.project_round.criteria_check_frozen:
        return HttpResponseForbidden()

    admission_result = AdmissionResult.get_for_application_and_major(application, major)
    if not admission_result:
        admission_result = AdmissionResult(applicant=applicant,
                                           application=application,
                                           admission_project=request.project,
                                           admission_round=admission_round,
                                           major=major)

    if decision == 'accepted':
        admission_result.is_criteria_passed = True
    else:
        admission_result.is_criteria_passed = False

    admission_result.updated_criteria_passed_at = datetime.now()
    admission_result.save()

    LogItem.create('Criteria decision (major: {0} {1}) by {2}'.format(major_number,
                                                                      decision,
                                                                      user.username),
                   applicant,
                   request)

    is_criteria_passed = admission_result.is_criteria_passed

    from django.template import loader
    template = loader.get_template('backoffice/projects/include/criteria_buttons.html')

    html = template.render({ 'is_criteria_passed': is_criteria_passed }, request)

    return HttpResponse(json.dumps({ 'result': 'OK',
                                     'html': html }),
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

def sort_applicants_by_calculated_scores(applicants, criteria_check_required):
    passed_applicants = [x[2] for x in
                         sorted([(-a.admission_result.calculated_score, a.national_id, a)
                                 for a in applicants if a.is_criteria_passed])]
    not_passed_applicants = [a for a in applicants if not a.is_criteria_passed]

    return passed_applicants + not_passed_applicants


def update_interview_call_status(applicants, decision):
    for a in applicants:
        if not decision:
            a.is_called_for_interview = False
        elif not a.is_interview_callable:
            a.is_called_for_interview = False
        else:
            a.is_called_for_interview = a.admission_result.calculated_score > (decision.interview_call_min_score - MajorInterviewCallDecision.FLOAT_DELTA)

            
@user_login_required
def show_scores(request, project_id, round_id, major_number):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)
    major = Major.get_by_project_number(project, major_number)

    if not can_user_view_applicants_in_major(user, project, major):
        return redirect(reverse('backoffice:index'))

    applicants = load_major_applicants(project, admission_round, major)
    
    applicant_score_viewable = project_round.applicant_score_viewable
    load_check_marks_and_results(applicants,
                                 project,
                                 admission_round,
                                 project_round)

    interview_call_count = 0
    if applicant_score_viewable:
        applicants = sort_applicants_by_calculated_scores(applicants,
                                                          project_round.criteria_check_required)
        call_decision = MajorInterviewCallDecision.get_for(major, admission_round)
        update_interview_call_status(applicants, call_decision)

        interview_call_count = len([a for a in applicants if a.is_called_for_interview])

    return render(request,
                  'backoffice/projects/show_applicant_scores.html',
                  { 'project': project,
                    'admission_round': admission_round,
                    'project_round': project_round,
                    'major': major,

                    'applicants': applicants,
                    'interview_call_count': interview_call_count,
                    
                    'applicant_score_viewable': applicant_score_viewable,
                    'accepted_for_interview_result_frozen':
                    project_round.accepted_for_interview_result_frozen,
                  })

@user_login_required
def update_interview_call_score(request, project_id, round_id, major_number):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)
    major = Major.get_by_project_number(project, major_number)

    if not can_user_view_applicants_in_major(user, project, major):
        return HttpResponseForbidden()

    applicant_score_viewable = project_round.applicant_score_viewable
    if not applicant_score_viewable:
        return HttpResponseForbidden()

    if project_round.accepted_for_interview_result_frozen:
        return HttpResponseForbidden()

    applicants = load_major_applicants(project, admission_round, major)
    load_check_marks_and_results(applicants,
                                 project,
                                 admission_round,
                                 project_round)

    applicants = sort_applicants_by_calculated_scores(applicants,
                                                      project_round.criteria_check_required)
    call_decision = MajorInterviewCallDecision.get_for(major, admission_round)
    update_interview_call_status(applicants, call_decision)
    if not call_decision:
        call_decision = MajorInterviewCallDecision(admission_round=admission_round,
                                                   major=major,
                                                   admission_project=project)

    national_id = request.POST['nationalId']
    selection_status = request.POST['status']

    selected_applicants = [a for a in applicants if a.national_id == national_id]
    if len(selected_applicants) == 0:
        return HttpResponseForbidden()

    applicant = selected_applicants[0]

    if not applicant.is_interview_callable:
        return HttpResponseForbidden()

    if selection_status == 'selected':
        if applicant.is_called_for_interview:
            return HttpResponseForbidden()

        call_decision.interview_call_min_score = applicant.admission_result.calculated_score
    else:
        if not applicant.is_called_for_interview:
            return HttpResponseForbidden()

        a_app = None
        for a in applicants:
            if a.is_interview_callable:
                if a.admission_result.calculated_score > applicant.admission_result.calculated_score:
                    a_app = a
        if a_app:
            call_decision.interview_call_min_score = a_app.admission_result.calculated_score
        else:
            call_decision.interview_call_min_score = applicant.admission_result.calculated_score + 1
            
    update_interview_call_status(applicants, call_decision)
    call_decision.interview_call_count = len([a for a in applicants if a.is_called_for_interview])

    from datetime import datetime
    call_decision.updated_at = datetime.now()
    call_decision.save()

    LogItem.create('Updated interview decision ({0}/{1}) to {2} by {3}'.format(major.number,
                                                                               project.id,
                                                                               call_decision.interview_call_min_score,
                                                                               user.username),
                   applicant,
                   request)

    return HttpResponse(str(call_decision.interview_call_count))
        

    
