# TEMPORARY HACK: majors whose final acceptance result is not finalized yet,
# even though their project round already has accepted_result_shown = True.
#
# - Applicants called for interview in one of these majors keep seeing the
#   interview-call result (not the final result) and cannot be dropped by
#   deactivate_project as "not accepted".
# - Staff can still edit acceptance for these majors in the backoffice.
#
# Entries are (admission_project_id, major number).  Remove an entry when the
# major is finalized; delete this module when the set is empty.
ACCEPTED_RESULT_PENDING_MAJORS = {
    (1, 69),
    (2, 94),
}


def is_major_accepted_result_pending(major):
    return (major.admission_project_id, major.number) in ACCEPTED_RESULT_PENDING_MAJORS


def is_accepted_result_shown_for(project_round, admission_results):
    """project_round.accepted_result_shown, except False when the applicant
    was called for interview in a pending major."""
    if not project_round.accepted_result_shown:
        return False
    for res in admission_results:
        if res.is_accepted_for_interview and is_major_accepted_result_pending(res.major):
            return False
    return True
