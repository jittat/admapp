from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, ButtonHolder, Row, Div

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject,ProjectApplication,EducationalProfile,PersonalProfile, Payment
from backoffice.models import Profile

from backoffice.decorators import user_login_required
from .permissions import can_user_view_project

from admapp.emails import send_forget_password_email

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
        admission_projects = profile.admission_projects.filter(is_available=True).all()
    if user.is_super_admin:
        is_admission_admin = True
        is_application_admin = True
        admission_projects = AdmissionProject.objects.filter(is_available=True).all()
        stats['applicant_count'] = Applicant.objects.count()
        stats['project_application_count'] = ProjectApplication.objects.filter(is_canceled=False).count()
    
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
    
    education = applicant.get_educational_profile()
    personal = applicant.get_personal_profile()
    payments = Payment.objects.filter(applicant=applicant)

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
    
