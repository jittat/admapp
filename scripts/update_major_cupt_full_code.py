from django_bootstrap import bootstrap
bootstrap()
import sys

from appl.models import Major, AdmissionRound, AdmissionProject, AdmissionProjectRound


def main():
    admission_round = AdmissionRound.objects.get(pk=sys.argv[1])

    admission_projects = [apr.admission_project for apr in AdmissionProjectRound.objects.filter(admission_round=admission_round)]

    count = 0
    for admission_project in admission_projects:
        for major in admission_project.major_set.all():
            try:
                full_code = major.detail_items_csv.split(",")[-2]
                major.cupt_full_code = full_code
                major.save()
                count += 1
                print(count, major)
            except:
                pass

    print('Updated', count, 'majors')
if __name__ == '__main__':
    main()
