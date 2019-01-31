import csv
import json
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from appl.models import Faculty, AdmissionRound
from backoffice.models import AdjustmentMajor

from backoffice.decorators import number_adjustment_login_required

def load_faculty_major_statistics(faculty, admission_rounds):
    adjustment_majors = (AdjustmentMajor.objects.
                         filter(faculty=faculty).order_by('full_code').all())

    for m in adjustment_majors:
        m.round_stats = [0] * len(admission_rounds)
    
    return adjustment_majors

@number_adjustment_login_required
def index(request):
    user = request.user
    
    if user.is_super_admin:
        faculties = Faculty.objects.all()
    else:
        faculties = [user.profile.faculty]

    admission_rounds = AdmissionRound.objects.all()
    
    for f in faculties:
        f.majors = load_faculty_major_statistics(f, admission_rounds)
        
    return render(request,
                  'backoffice/adjustment/index.html',
                  { 'faculties': faculties,
                    'admission_rounds': admission_rounds, })
