import json

from django.shortcuts import render, redirect
from django import forms
from django.forms import ModelForm
from django.http import HttpResponse

from regis.decorators import appl_login_required

from regis.models import Applicant
from appl.models import Province, School
from appl.models import PersonalProfile, EducationalProfile


class EducationForm(ModelForm):
    class Meta:
        model = EducationalProfile
        exclude = ['applicant',
                   'school_code']

    
class PersonalProfileForm(ModelForm):
    class Meta:
        model = PersonalProfile
        exclude = ['applicant']


@appl_login_required
def ajax_school_search(request):
    province = request.GET['province']
    term = request.GET['term']
    schools = School.objects.filter(province=province,title__contains=term)
    results = [s.title for s in schools]
    return HttpResponse(json.dumps(results))


@appl_login_required        
def personal_profile(request):
    applicant = request.applicant
    try:
        profile = applicant.personalprofile
    except PersonalProfile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = PersonalProfileForm(request.POST, instance=profile)
        if form.is_valid():
            new_personal_profile = form.save(commit=False)
            new_personal_profile.applicant = applicant
            new_personal_profile.save()
            return redirect('/appl/')
    else:
        form = PersonalProfileForm(instance=profile)

    return render(request, 'appl/forms/personal.html',
                  { 'form': form })


@appl_login_required        
def education_profile(request):
    applicant = request.applicant
    try:
        profile = applicant.educationalprofile
    except EducationalProfile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = EducationForm(request.POST, instance=profile)
        if form.is_valid():
            new_educational_profile = form.save(commit=False)
            new_educational_profile.applicant = applicant
            province = new_educational_profile.province
            school_title = new_educational_profile.school_title
            schools = School.objects.filter(province=province,
                                            title=school_title).all()
            if len(schools) >= 1:
                school = schools[0]
                new_educational_profile.school_code = school.code

            new_educational_profile.save()
            return redirect('/appl/')
    else:
        form = EducationForm(instance=profile)

    return render(request, 'appl/forms/education.html',
                  { 'form': form })
