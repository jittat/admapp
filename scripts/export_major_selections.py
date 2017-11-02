from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionRound, Applicant, ProjectApplication

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
            items = [app.applicant.national_id]
            items += app.major_selection.get_major_numbers()
            print(','.join([str(x) for x in items]))
        

if __name__ == '__main__':
    main()
    
