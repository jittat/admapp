import json

from django.shortcuts import render, redirect
from django import forms
from django.forms import ModelForm
from django.http import HttpResponse
from django.urls import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit

from regis.decorators import appl_login_required

from regis.models import Applicant
from appl.models import Province, School
from appl.models import PersonalProfile, EducationalProfile


class EducationForm(ModelForm):
    class Meta:
        model = EducationalProfile
        exclude = ['applicant',
                   'school_code']

class ThaiSelectDateWidget(forms.widgets.SelectDateWidget):
    def get_context(self, name, value, attrs):
        context = super(ThaiSelectDateWidget, self).get_context(name,
                                                                value,
                                                                attrs)
        print(context)
        date_context = {}
        year_choices = [(i, str(i+543)) for i in self.years]
        if self.is_required is False:
            year_choices.insert(0, self.year_none_value)
        year_attrs = context['widget']['attrs'].copy()
        year_name = self.year_field % name
        year_attrs['id'] = 'id_%s' % year_name
        date_context['year'] = self.select_widget(attrs, choices=year_choices).get_context(
            name=year_name,
            value=context['widget']['value']['year'],
            attrs=year_attrs,
        )

        print(context)
        context['widget']['subwidgets'][2] = date_context['year']['widget']

        return context
        
class PersonalProfileForm(ModelForm):
    class Meta:
        model = PersonalProfile
        exclude = ['applicant']
        widgets = {
            'birthday': ThaiSelectDateWidget(years=range(1990,2010))
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Fieldset(
                'ข้อมูลส่วนตัว',
                'prefix_english',
                'first_name_english',
                'middle_name_english',
                'last_name_english',
                'passport_number',
                'birthday',
            ),
            Fieldset(
                'ข้อมูลบิดา',
                'father_prefix',
                'father_first_name',
                'father_last_name',
            ),
            Fieldset(
                'ข้อมูลมารดา',
                'mother_prefix',
                'mother_first_name',
                'mother_last_name',
            ),
            Fieldset(
                'ข้อมูลที่อยู่',
                'house_number',
                'village_number',
                'avenue',
                'road',
                'sub_district',
                'district',
                'province',
                'postal_code',
                'contact_phone',
                'mobile_phone',
            ),
            ButtonHolder(
                Submit('submit', 'จัดเก็บ', css_class='btn btn-primary')
            )
        )


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
    profile = applicant.get_personal_profile()

    if request.method == 'POST':
        form = PersonalProfileForm(request.POST, instance=profile)
        if form.is_valid():
            new_personal_profile = form.save(commit=False)
            new_personal_profile.applicant = applicant
            new_personal_profile.save()
            return redirect(reverse('appl:index'))
    else:
        form = PersonalProfileForm(instance=profile)

    return render(request, 'appl/forms/personal.html',
                  { 'form': form })


@appl_login_required        
def education_profile(request):
    applicant = request.applicant
    profile = applicant.get_educational_profile()

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
            else:
                new_educational_profile.school_code = ''

            new_educational_profile.save()
            return redirect(reverse('appl:index'))
    else:
        form = EducationForm(instance=profile)

    return render(request, 'appl/forms/education.html',
                  { 'form': form })
