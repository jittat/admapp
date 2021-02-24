from django.http import HttpResponseForbidden

from regis.models import Applicant
from appl.models import AdmissionProject
from backoffice.models import Profile

def is_super_admin(user):
    return user.is_staff

def is_number_adjustment_admin(user):
    profile = Profile.get_profile_for(user)

    if not profile:
        return False
    return profile.is_number_adjustment_admin

def can_user_view_project(user, project):
    if is_super_admin(user):
        return True

    profile = Profile.get_profile_for(user)

    if not profile:
        return False

    return profile.admission_projects.filter(id=project.id).count() == 1


def can_user_view_applicants_in_major(user, project, major):
    if is_super_admin(user):
        return True

    profile = Profile.get_profile_for(user)

    if not profile:
        return False

    if profile.admission_projects.filter(id=project.id).count() == 1:
        if profile.is_admission_admin:
            return True
        else:
            if major.faculty_id == profile.faculty_id:
                return ((profile.major_number == major.number) or
                        (profile.major_number == profile.ANY_MAJOR))
            else:
                return False
    else:
        return False


def can_user_view_applicant_in_major(user, applicant, application, project, major):
    if not can_user_view_applicants_in_major(user, project, major):
        return False
    return True

def can_user_adjust_major(user, major):
    if is_super_admin(user):
        return True
    
    profile = Profile.get_profile_for(user)

    if not profile:
        return False

    return (profile.faculty == major.faculty and
            (profile.adjustment_major_number == '0' or
             profile.adjustment_major_number == major.full_code))

def can_user_confirm_major_adjustment(user, major):
    if is_super_admin(user):
        return True
    
    profile = Profile.get_profile_for(user)

    if not profile:
        return False

    return (profile.faculty == major.faculty and
            (profile.adjustment_major_number == '0'))
