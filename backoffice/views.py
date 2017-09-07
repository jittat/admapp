from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from appl.models import AdmissionProject

@login_required
def index(request):
    user = request.user
    try:
        profile = user.profile
    except:
        profile = None

    is_admission_admin = False
    faculty = None
    admission_projects = []
    
    if profile:
        faculty = profile.faculty
        is_admission_admin = profile.is_admission_admin
        admission_projects = profile.admission_projects.all()
    if user.is_staff:
        is_admission_admin = True
        admission_projects = AdmissionProject.objects.all()
    
    return render(request,
                  'backoffice/index.html',
                  { 'admission_projects': admission_projects,
                    'faculty': faculty,
                    'is_admission_admin': is_admission_admin })

