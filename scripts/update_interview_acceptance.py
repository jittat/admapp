from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionRound, MajorInterviewDescription, AdmissionResult

from regis.models import LogItem

def main():
    project = AdmissionProject.objects.get(pk=sys.argv[1])
    admission_round = AdmissionRound.objects.get(pk=2)

    majors = project.major_set.all()

    for m in majors:
        try:
            interview_description = MajorInterviewDescription.objects.get(major=m,
                                                                          admission_round=admission_round)
        except:
            print('>> Interview not found', m)
            continue

        if not interview_description.has_free_acceptance:
            continue

        admission_results = AdmissionResult.objects.filter(major=m,
                                                           is_accepted_for_interview=True).all()

        rejected_results = [res for res in admission_results
                            if res.is_accepted == False]
        if len(rejected_results) != 0:
            print('ERROR some has been rejected... ',m)
            continue

        count = 0
        for res in admission_results:
            res.is_accepted = True
            res.is_interview_absent = False
            applicant = res.applicant

            LogItem.create('auto accept', applicant=applicant)
            res.save()
            count += 1

        if count > 0:
            print(f'{m} - {count} accepted')

if __name__ == '__main__':
    main()
    
