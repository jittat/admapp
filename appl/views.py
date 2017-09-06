from django.shortcuts import render

from regis.models import Applicant
from regis.decorators import appl_login_required


@appl_login_required
def index(request):
    return render(request,
                  'appl/index.html',
                  { 'applicant': request.applicant })

        
