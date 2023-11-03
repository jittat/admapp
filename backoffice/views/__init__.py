from django import forms
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from admapp.emails import send_forget_password_email
from appl.models import AdmissionProject, ProjectApplication, Payment
from backoffice.decorators import user_login_required, super_admin_login_required
from backoffice.models import Profile
from regis.models import Applicant, LogItem, CuptRequestQueueItem
from supplements.models import load_supplement_configs_with_instance
from supplements.views import render_supplement_for_backoffice
from .permissions import can_user_view_project


class ApplicantForm(forms.Form):
    email = forms.EmailField(label='อีเมล')
    prefix = forms.ChoiceField(label='คำนำหน้า',
                               choices=[('นาย','นาย'),
                                        ('นางสาว','นางสาว'),
                                        ('นาง','นาง')])
    first_name = forms.CharField(label='ชื่อ',
                                 max_length=100)
    last_name = forms.CharField(label='นามสกุล',
                                max_length=200)


def compute_project_stats(admission_projects):
    stat_keys = {}
    
    for project in admission_projects:
        admission_round_stats = []
        c = 0
        for r in project.admission_rounds.all():
            stats = {'num_applicants': 0}
            admission_round_stats.append((r, stats))

            stat_keys[(project.id, r.id)] = (project, c)

            c += 1
            
        project.admission_round_stats = admission_round_stats

    applications = ProjectApplication.objects.filter(is_canceled=False).all()
    for a in applications:
        k = (a.admission_project_id, a.admission_round_id)
        if k in stat_keys:
            project, c = stat_keys[k]
            project.admission_round_stats[c][1]['num_applicants'] += 1

            
def sort_admission_projects(admission_projects):
    return [p for _,_,p in sorted([(p.admission_rounds.all()[0].id, p.id,p) for p in admission_projects])]


def compute_cupt_confirmation_stats():
    counters = {}
    for a in Applicant.objects.prefetch_related('cupt_confirmation').all():
        if a.has_cupt_confirmation_result():
            code = a.cupt_confirmation.api_result_code
        else:
            code = -1
        if code not in counters:
            counters[code] = 0
        counters[code] += 1
    return {
        'counters': [(k,counters[k]) for k in sorted(counters.keys())],
        'queue_count': CuptRequestQueueItem.objects.count(),
    }
            
@user_login_required
def index(request):
    user = request.user
    profile = Profile.get_profile_for(user)

    is_admission_admin = False
    is_application_admin = False
    faculty = None
    admission_projects = []
    stats = {}
    
    if profile:
        faculty = profile.faculty
        is_admission_admin = profile.is_admission_admin
        admission_projects = profile.admission_projects.filter(Q(is_available=True) | Q(is_visible_in_backoffice=True)).all()
    if user.is_super_admin:
        is_admission_admin = True
        is_application_admin = True
        admission_projects = AdmissionProject.objects.filter(Q(is_available=True) | Q(is_visible_in_backoffice=True)).all()
        stats['applicant_count'] = Applicant.objects.count()
        stats['confirmation'] = compute_cupt_confirmation_stats()
        stats['project_application_count'] = ProjectApplication.objects.filter(is_canceled=False).count()

    admission_projects = sort_admission_projects(admission_projects)
        
    compute_project_stats(admission_projects)
        
    return render(request,
                  'backoffice/index.html',
                  { 'admission_projects': admission_projects,
                    'faculty': faculty,

                    'is_admission_admin': is_admission_admin,
                    'is_application_admin': is_application_admin,

                    'applicant_stats': stats,
                  })


@user_login_required
def search(request, project_id=None):
    user = request.user
    if not user.is_super_admin:
        return HttpResponseForbidden()

    query = request.POST['q']
    applicants = Applicant.find_by_query(query)

    if (len(query.strip())==6) and (user.is_super_admin):
        application = ProjectApplication.find_by_number(query.strip())
        if application:
            applicants.append(application.applicant)

    message = ''
    if len(applicants) > 200:
        message = 'แสดงเฉพาะ 200 คนแรก'
        applicants = applicants[:200]

    if len(applicants) == 1:
        return redirect(reverse('backoffice:show-applicant', args=[applicants[0].national_id]))
        
    return render(request,
                  'backoffice/search.html',
                  { 'query': query,
                    'applicants': applicants,
                    'message': message,
                  })

 
@user_login_required
def show(request, national_id, project_id=None):
    user = request.user
    
    if project_id:
        project = get_object_or_404(AdmissionProject, pk=project_id)
    else:
        project = None
        
    if not user.is_super_admin:
        if project_id==None:
            return HttpResponseForbidden()

        if not can_user_view_project(user, project):
            return redirect(reverse('backoffice:index'))

    applicant = get_object_or_404(Applicant, national_id=national_id)
    all_applications = applicant.get_all_active_applications()

    applications = []
    for a in all_applications:
        if user.is_super_admin or a.admission_project_id == int(project_id):
            applications.append(a)

    if (not user.is_super_admin) and len(applications)==0:
        return redirect(reverse('backoffice:index'))

    if (not user.is_super_admin) and (not user.profile.is_admission_admin):
        applied = False
        for a in applications:
            if a.has_applied_to_faculty(user.profile.faculty):
                applied = True
                break
        if not applied:
            return redirect(reverse('backoffice:index'))
    
    education = applicant.get_educational_profile()
    personal = applicant.get_personal_profile()
    payments = Payment.objects.filter(applicant=applicant)

    for app in applications:
        supplement_configs = load_supplement_configs_with_instance(applicant,
                                                                       app.admission_project)
        for c in supplement_configs:
            if hasattr(c,'supplement_instance'):
                c.html = render_supplement_for_backoffice(c, c.supplement_instance)
            else:
                c.html = None
                
        app.supplement_configs = supplement_configs
        
    if user.is_super_admin:
        logs = applicant.logitem_set.all()
        applicant_form = ApplicantForm(initial={'email': applicant.email,
                                                'prefix': applicant.prefix,
                                                'first_name': applicant.first_name,
                                                'last_name': applicant.last_name})
    else:
        logs = []
        applicant_form = None

    notice = request.session.pop('notice', None)
        
    return render(request,
                  'backoffice/show.html',
                  { 'applicant': applicant,
                    'education': education,
                    'personal': personal,

                    'applicant_form': applicant_form,
                    
                    'applications': applications,
                    'payments': payments,

                    'logs': logs,
                    'notice': notice,
                  })


@user_login_required
def cancel_confirmed_application(request, national_id):
    user = request.user
    if not request.method == 'POST':
        return HttpResponseForbidden()
    if not user.is_super_admin:
        return HttpResponseForbidden()

    applicant = get_object_or_404(Applicant, national_id=national_id)

    if applicant.confirmed_application_id != None:
        LogItem.create('Removed confirmed application ({0})'.format(applicant.confirmed_application_id), applicant, request)
    
        applicant.confirmed_application_id = None
        applicant.save()

    return redirect(reverse('backoffice:show-applicant', args=[applicant.national_id]))


@user_login_required
def new_password(request, national_id):
    user = request.user
    
    if not user.is_super_admin:
        return HttpResponseForbidden()

    applicant = get_object_or_404(Applicant, national_id=national_id)
    new_password = applicant.random_password()
    applicant.save()

    LogItem.create('Admin new password requested ({0})'.format(user.username), applicant, request)
                
    send_forget_password_email(applicant, new_password)

    request.session['notice'] = 'เปลี่ยนรหัสผ่านและส่งให้ผู้สมัครแล้ว รหัสผ่านคือ {0} (สามารถส่งให้ผู้สมัครทางเมลได้)'.format(new_password)
    return redirect(reverse('backoffice:show-applicant', args=[applicant.national_id]))
    

@user_login_required
def update_applicant(request, national_id):
    user = request.user
    
    if not user.is_super_admin:
        return HttpResponseForbidden()

    applicant = get_object_or_404(Applicant, national_id=national_id)

    form = ApplicantForm(request.POST)
    if form.is_valid():
        old_first_name = applicant.first_name
        old_last_name = applicant.last_name
        old_email = applicant.email
        
        applicant.prefix = form.cleaned_data['prefix']
        applicant.first_name = form.cleaned_data['first_name']
        applicant.last_name = form.cleaned_data['last_name']
        applicant.email = form.cleaned_data['email']

        if applicant.email != old_email:
            new_password = applicant.random_password()
        
        applicant.save()

        if applicant.email != old_email:
            send_forget_password_email(applicant, new_password)

        LogItem.create('Admin updated applicant (from: {0}/{1}/{2})'.format(old_first_name, old_last_name, old_email), applicant, request)
                
        if applicant.email == old_email:
            request.session['notice'] = 'แก้ไขข้อมูลเรียบร้อยแล้ว'
        else:
            request.session['notice'] = 'แก้ไขข้อมูลและส่งเมลแจ้งผู้สมัครเรียบร้อยแล้ว'
    else:
        request.session['notice'] = 'ไม่สามารถแก้ไขข้อมูลได้ เกิดความผิดพลาดในฟอร์ม'
        
    return redirect(reverse('backoffice:show-applicant', args=[applicant.national_id]))
    
@super_admin_login_required
def login_as_applicant(request, national_id, login_key):
    from django.conf import settings

    try:
        if login_key != settings.SUPER_ADMIN_APPLICANT_LOGIN_KEY:
            return HttpResponseForbidden()
    except:
        return HttpResponseForbidden()

    applicant = get_object_or_404(Applicant, national_id=national_id)
    
    from regis.views import login_applicant

    login_applicant(request, applicant)

    LogItem.create('Admin ({0}) logged in as {1}'.format(request.user.username, applicant.national_id), applicant, request)
                
    return redirect(reverse('appl:index'))

