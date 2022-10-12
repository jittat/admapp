from django_bootstrap import bootstrap
bootstrap()

from regis.models import LogItem
from appl.models import AdmissionProject, AdmissionRound, ProjectApplication

def main():
    project_id = 11
    round_id = 2

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    applications = ProjectApplication.objects.filter(admission_project=admission_project,
                                                     admission_round=admission_round,
                                                     is_canceled=False).all()

    for a in applications:
        app = a.applicant
        last_log = LogItem.get_applicant_latest_log(app, 'appllog:sport-confirm-option')

        if last_log:
            print(",".join([app.national_id, last_log.message[-1]]))


if __name__ == '__main__':
    main()
    
