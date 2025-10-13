from django_bootstrap import bootstrap
bootstrap()
import sys

from appl.models import Major, AdmissionRound, AdmissionProject, AdmissionProjectRound
from appl.models import MajorAdditionalNotice, MajorAdditionalAdmissionFormField
from criteria.models import MajorCuptCode

def update_notice(admission_project, major, criterias):
    additional_notices = []
    for criteria in criterias:
        if criteria.additional_notice != '':
            additional_notices.append(criteria.additional_notice)

    additional_notice_str = '\n'.join(additional_notices)            
    if len(additional_notices) != 0:
        print(admission_project, major, additional_notice_str)

        old_notice = MajorAdditionalNotice.get_notice_by_major(major)
        if old_notice:
            notice = old_notice
        else:
            notice = MajorAdditionalNotice()
            notice.major = major

        notice.message = additional_notice_str
        notice.save()

        return True
    else:
        return False

def update_form(admission_project, major, criterias):
    all_form_fields = []
    for c in criterias:
        form_fields = c.get_additional_admission_form_fields()
        if form_fields:
            all_form_fields.append(form_fields)
    
    if len(all_form_fields) > 1:
        print("ERROR too many additional form fields", admission_project, major, all_form_fields)
        form_fields = all_form_fields[0]
    elif len(all_form_fields) == 1:
        form_fields = all_form_fields[0]
    else:
        form_fields = None

    if not form_fields:
        return False

    old_form_fields = list(major.additionaladmissionformfields.all())
    for i, field in enumerate(form_fields):
        if i < len(old_form_fields):
            field = old_form_fields[i]
        else:
            field = MajorAdditionalAdmissionFormField()
        field.major = major
        field.title = form_fields[i]['title']
        field.size = form_fields[i]['size']
        field.rank = i+1
        field.save()

    if len(old_form_fields) > len(form_fields):
        print("ERROR too many old fields", admission_project, major, old_form_fields, form_fields)

    return True

def main():
    admission_round = AdmissionRound.objects.get(pk=sys.argv[1])

    admission_projects = [apr.admission_project for apr in AdmissionProjectRound.objects.filter(admission_round=admission_round)]

    notice_count = 0
    form_count = 0
    for admission_project in admission_projects:
        for major in admission_project.major_set.all():
            cupt_code = MajorCuptCode.get_from_full_code(major.cupt_full_code)
            if not cupt_code:
                continue
            
            curriculum_majors = cupt_code.curriculummajor_set.filter(admission_project=admission_project).all()
            if not curriculum_majors:
                continue

            criterias = []
            for cm in curriculum_majors:
                for criteria in cm.admission_criterias.filter(is_deleted=False).all():
                    criterias.append(criteria)

            is_updated = update_notice(admission_project, major, criterias)
            if is_updated:
                notice_count += 1

            is_updated = update_form(admission_project, major, criterias)
            if is_updated:
                form_count += 1

    print('Notice updated', notice_count, 'majors')
    print('Form updated', form_count, 'majors')


if __name__ == '__main__':
    main()
