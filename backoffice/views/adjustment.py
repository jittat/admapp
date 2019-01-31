import csv
import json
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from appl.models import Faculty, AdmissionRound
from backoffice.models import AdjustmentMajor, AdjustmentMajorSlot

from backoffice.decorators import number_adjustment_login_required

def load_faculty_major_statistics(faculty, admission_rounds):
    adjustment_majors = (AdjustmentMajor.objects.
                         filter(faculty=faculty).order_by('full_code').all())

    mmap = {}
    for m in adjustment_majors:
        m.round_stats = [0] * len(admission_rounds)
        mmap[m.full_code] = m

    for slot in AdjustmentMajorSlot.objects.filter(faculty=faculty).all():
        m = mmap[slot.major_full_code]
        m.round_stats[slot.admission_round_number - 1] += slot.current_slots
        
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
