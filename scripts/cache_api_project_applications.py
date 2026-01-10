from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import ProjectApplication, MajorSelection

def main():
    applications = (ProjectApplication.objects
                    .filter(is_canceled=False)
                    .select_related('major_selection').all())

    counter = 0
    for application in applications:
        old_cached_num_majors = application.cached_num_majors
        old_cached_has_paid = application.cached_has_paid

        if hasattr(application, 'major_selection'):
            major_selection = application.major_selection
            application.cached_num_majors = major_selection.num_selected
            admission_fee = application.admission_fee(major_selection=major_selection)
        else:
            application.cached_num_majors = 0
            admission_fee = application.admission_fee(majors=[])
        application.cached_has_paid = application.has_paid_min(admission_fee)

        if (old_cached_num_majors != application.cached_num_majors or 
            old_cached_has_paid != application.cached_has_paid):
            application.save(update_fields=['cached_num_majors', 'cached_has_paid'])

        counter += 1
        if counter % 1000 == 0:
            print(f"Processed {counter} applications")

    print(f"Finished processing {counter} applications")

if __name__ == '__main__':
    main()
