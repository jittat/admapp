from django.shortcuts import render, redirect
from django import forms
from django.forms import ModelForm

from regis.decorators import appl_login_required

from regis.models import Applicant
from appl.models import Province, School
from appl.models import PersonalProfile


class EducationForm(forms.Form):
    education_level = forms.ChoiceField(label='ระดับการศึกษา', 
                                        choices=[('กำลังศึกษาชั้นมัธยมศึกษาปีที่ 6','กำลังศึกษาชั้นมัธยมศึกษาปีที่ 6'),
                                                ('จบการศึกษาชั้นมัธยมศึกษาปีที่ 6','จบการศึกษาชั้นมัธยมศึกษาปีที่ 6'),
                                                ('อื่นๆ','อื่นๆ')])
    education_plan = forms.ChoiceField(label='แผนการศึกษา',
                                        choices=[('วิทย์-คณิต','วิทย์-คณิต'),
                                                ('อื่นๆ','อื่นๆ')])
    gpa = forms.CharField(label='GPA',max_length=10)

    province_title = forms.CharField(label='จังหวัด', max_length=30)
    school_titile = forms.CharField(label='ชื่อโรงเรียน', max_length=80)


class PersonalProfileForm(ModelForm):
    class Meta:
        model = PersonalProfile
        fields = ['mobile_phone']


@appl_login_required        
def education_profile(request):
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            return render(request,'form/test.html',
			  { 'province_title': form.cleaned_data['province_title'],
                'school_title': form.cleaned_data['school_title'],
                'education_level': form.cleaned_data['education_level'],
                'education_plan': form.cleaned_data['education_plan'],
                'gpa': form.cleaned_data['gpa'] })
    else:
        form = EducationForm()
            
    return render(request, 'appl/forms/education.html',
                  { 'form':form })


@appl_login_required        
def personal_profile(request):
    if request.method == 'POST':
        form = PersonalProfileForm(request.POST)
        if form.is_valid():
            return redirect('/thanks/')

    else:
        form = PersonalProfileForm()

    return render(request, 'appl/forms/personal.html',
                  { 'form': form })
