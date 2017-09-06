from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse

from .models import Applicant

def appl_login_required(view_function):

    def login_required_view_function(request):
        if 'applicant_id' not in request.session:
            return redirect(reverse('main-index') + '?error=no-login')

        applicant_id = request.session['applicant_id']
        applicant = get_object_or_404(Applicant,pk=applicant_id)

        request.applicant = applicant

        return view_function(request)

    return login_required_view_function
