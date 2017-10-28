from supplements.models import AdvancedPlacementApplicant, AdvancedPlacementResult

def load_ap_course_results(applicant, admission_project, admission_round):
    try:
        app = AdvancedPlacementApplicant.objects.get(national_id=applicant.national_id)
    except:
        app = None

    if not app:
        return {'courses': []}

    return {'courses': app.results.all()}
