from django.shortcuts import render, redirect
from django import forms
from django.forms import ModelForm

from regis.decorators import appl_login_required

from regis.models import Applicant
from appl.models import Province, School
from appl.models import PersonalProfile


class EducationForm(forms.Form):
    province_name = forms.CharField(label='จังหวัด', max_length=30)
    school_name = forms.CharField(label='ชื่อโรงเรียน', max_length=80)

class PersonalProfileForm(ModelForm):
    class Meta:
        model = PersonalProfile
        exclude = ['applicant']


@appl_login_required        
def education_profile(request):
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            return render(request,'form/test.html',
			  { 'province_name': form.cleaned_data['province_name'],
                            'school_name': form.cleaned_data['school_name'] })
    else:
        form = EducationForm()
            
    return render(request, 'appl/forms/education.html',
                  { 'form':form })


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
