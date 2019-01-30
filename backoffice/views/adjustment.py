import csv
import json
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from appl.models import Faculty

from backoffice.decorators import number_adjustment_login_required

@number_adjustment_login_required
def index(request):
    user = request.user
    
    if user.is_super_admin:
        faculties = Faculty.objects.all()
    else:
        faculties = [user.profile.faculty]
    
    return render(request,
                  'backoffice/adjustment/index.html',
                  { 'faculties': faculties, })
