from django_bootstrap import bootstrap
bootstrap()

import sys

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionRound, ProjectApplication

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    project_applications = ProjectApplication.find_for_project_and_round(project,
                                                                         admission_round,
                                                                         True)

    for app in project_applications:
        if app.has_paid():
            majors =  app.major_selection.get_majors()
            applicant = app.applicant
            if applicant.has_registered_with_passport():
                nat = applicant.passport_number
            else:
                nat = applicant.national_id
            profile = applicant.get_personal_profile()
            app_date = '%02d/%02d/%04d' % (app.applied_at.day,
                                     app.applied_at.month,
                                     app.applied_at.year + 543)
            for m in majors:
                items = [
                    m.get_full_major_cupt_code(),
                    m.faculty.title,
                    m.title,
                    project.title,
                    app.get_number(),
                    nat,
                    applicant.prefix,
                    applicant.first_name,
                    applicant.last_name,
                    profile.contact_phone,
                    applicant.email,
                    app_date,
                ]
                print(','.join(['"'+str(x)+'"' for x in items]))
        

if __name__ == '__main__':
    main()
    
