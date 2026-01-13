from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionRound
from appl.models import AdmissionProject, Major
from appl.models import ProjectApplication, MajorSelection, AdmissionResult
from backoffice.models import AdjustmentMajorSlot

def main():
    applications = (ProjectApplication.objects
                    .filter(is_canceled=False)
                    .select_related('major_selection').all())

    adjustment_major_slots = {
        s.cupt_code: s 
        for s 
        in AdjustmentMajorSlot.objects.all()
    }

    for slot in adjustment_major_slots.values():
        slot.new_num_applications = 0
        slot.new_num_accepted_applications = 0

    majors = {
        (m.admission_project_id, m.number): m
        for m in Major.objects.all()
    }

    admission_results = {
        (r.application_id, r.admission_project_id, r.major_id): r 
        for r in AdmissionResult.objects.all()
    }

    admission_projects = {
        p.id: p
        for p in AdmissionProject.objects.all()
    }

    admission_round_counts = {
        r.id: 0
        for r in AdmissionRound.objects.all()
    }

    counter = 0
    for application in applications:
        old_cached_num_majors = application.cached_num_majors
        old_cached_has_paid = application.cached_has_paid

        if hasattr(application, 'major_selection'):
            major_selection = application.major_selection
            application.cached_num_majors = major_selection.num_selected
            admission_fee = application.admission_fee(major_selection=major_selection)
        else:
            major_selection = None
            application.cached_num_majors = 0
            admission_fee = application.admission_fee(majors=[])
        application.cached_has_paid = application.has_paid_min(admission_fee)

        if (old_cached_num_majors != application.cached_num_majors or 
            old_cached_has_paid != application.cached_has_paid):
            application.save(update_fields=['cached_num_majors', 'cached_has_paid'])

        if major_selection:
            selected_majors = [
                majors.get((application.admission_project_id, num), None)
                for num in major_selection.get_major_numbers()
            ]
            results = [
                admission_results.get((application.id,
                                       application.admission_project_id,
                                       majors[(application.admission_project_id, num)].id), 
                                       None)
                for num in major_selection.get_major_numbers()
            ]
        else:
            selected_majors = []
            results = []

        admission_round_counts[application.admission_round_id] += 1
        for m,r in zip(selected_majors, results):
            if not m:
                continue
            admission_project = admission_projects[m.admission_project_id]
            full_cupt_code = f'{admission_project.cupt_code}{m.cupt_full_code}'
            if full_cupt_code in adjustment_major_slots:
                slot = adjustment_major_slots[full_cupt_code]
                slot.new_num_applications += 1
                if r and r.is_accepted:
                    slot.new_num_accepted_applications += 1
            else:
                print(m)
                print(r)
                print('Not found:', full_cupt_code)
                quit()

        counter += 1
        if counter % 1000 == 0:
            print(f"Processed {counter} applications")

    print(f"Finished processing {counter} applications")

    slot_updated = 0
    for slot in adjustment_major_slots.values():
        if ((admission_round_counts.get(slot.admission_round_id,0) != 0) and
            (slot.new_num_applications != slot.num_applications or
             slot.new_num_accepted_applications != slot.num_accepted_applications)):
            #print(slot,
            #      slot.num_applications, '->', slot.new_num_applications,
            #      slot.num_accepted_applications, '->', slot.new_num_accepted_applications)
            slot.num_applications = slot.new_num_applications
            slot.num_accepted_applications = slot.new_num_accepted_applications
            slot.save(update_fields=['num_applications', 'num_accepted_applications'])
            slot_updated += 1

    print(f"Finished updating {slot_updated} slots")

if __name__ == '__main__':
    main()
