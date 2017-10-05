from django.http import HttpResponseForbidden

from regis.models import Applicant
from appl.models import AdmissionProject
from backoffice.models import Profile

def can_user_view_project(user, project):
    if user.is_staff:
        return True

    profile = Profile.get_profile_for(user)

    if not profile:
        return False
    
    if profile.is_admission_admin: 
        print(profile.admission_projects.all())
        return profile.admission_projects.filter(id=project.id).count() == 1
    else:
        return False

    
    