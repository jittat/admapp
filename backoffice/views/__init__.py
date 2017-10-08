from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from regis.models import Applicant
from appl.models import AdmissionProject,ProjectApplication,EducationalProfile,PersonalProfile
from backoffice.models import Profile

@login_required
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
    if user.is_staff:
        is_admission_admin = True
        is_application_admin = True
        admission_projects = AdmissionProject.objects.filter(is_available=True).all()
        project_application = ProjectApplication.objects.filter(is_canceled=False).count()
        stats['applicant_count'] = Applicant.objects.count()
    
    return render(request,
                  'backoffice/index.html',
                  { 'admission_projects': admission_projects,
                    'faculty': faculty,
                    'is_admission_admin': is_admission_admin,
                    'is_application_admin': is_application_admin,
                    'applicant_stats': stats,
                    'project_application': project_application    
                    })


@login_required
def search(request, project_id=None):
    user = request.user
    if (project_id==None) and (not user.is_staff):
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
                    'message': message })

 
@login_required
def show(request, national_id, project_id=None):
    user = request.user
    if (project_id==None) and (not user.is_staff):
        return HttpResponseForbidden()

    applicant = get_object_or_404(Applicant, national_id=national_id)
    education = applicant.get_educational_profile()

    return render(request,
                  'backoffice/show.html',
                  { 'applicant': applicant,
                    'education': education, })


    
    
    

    





