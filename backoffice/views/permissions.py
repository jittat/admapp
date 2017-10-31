from django.http import HttpResponseForbidden

from regis.models import Applicant
from appl.models import AdmissionProject
from backoffice.models import Profile

def is_super_admin(user):
    return user.is_staff

def can_user_view_project(user, project):
    if is_super_admin(user):
        return True

    profile = Profile.get_profile_for(user)

    if not profile:
        return False
    
    return profile.admission_projects.filter(id=project.id).count() == 1

def can_user_view_applicant_in_major(user, applicant, application, project, major):
    if is_super_admin(user):
        return True

    profile = Profile.get_profile_for(user)

    if not profile:
        return False

    if profile.admission_projects.filter(id=project.id).count() == 1:
        if profile.is_admission_admin:
            return True
        else:
            return major.faculty_id == profile.faculty_id
    else:
        return False
    
