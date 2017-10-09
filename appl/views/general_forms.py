import json

from django.shortcuts import render, redirect
from django import forms
from django.forms import ModelForm
from django.http import HttpResponse
from django.urls import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, MultiWidgetField, Div, Row

from regis.decorators import appl_login_required

from regis.models import Applicant
from appl.models import Province, School
from appl.models import PersonalProfile, EducationalProfile


class EducationForm(ModelForm):
    class Meta:
        model = EducationalProfile
        exclude = ['applicant',
                   'school_code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'จัดเก็บ', css_class='btn btn-primary'))


class ThaiSelectDateWidget(forms.widgets.SelectDateWidget):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
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
        context['widget']['subwidgets'][2] = date_context['year']['widget']
        return context


class PersonalProfileForm(ModelForm):
    class Meta:
        model = PersonalProfile
        labels = {
            'prefix_english': 'คำนำหน้า',
            'first_name_english': 'ชื่อต้น',
            'middle_name_english': 'ชื่อกลาง (ถ้ามี)',
            'last_name_english': 'นามสกุล',
            'father_prefix': 'คำนำหน้า',
            'father_first_name': 'ชื่อต้น',
            'father_last_name': 'นามสกุล',
            'mother_prefix': 'คำนำหน้า',
            'mother_first_name': 'ชื่อต้น',
            'mother_last_name': 'นามสกุล',
        }
        exclude = ['applicant']
        widgets = {
            'birthday': ThaiSelectDateWidget(years=range(1990,2010))
        }

    def _show_passport_field(self):
        if self.instance.applicant.passport_number:
            return None
        return 'passport_number'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'ข้อมูลผู้สมัครภาษาอังกฤษ',
                Row(
                    Div('prefix_english', css_class='col-md-2'),
                    Div('first_name_english', css_class='col-md-3'),
                    Div('middle_name_english', css_class='col-md-3'),
                    Div('last_name_english', css_class='col-md-4'),
                ),
            ),
            Fieldset(
                'ข้อมูลส่วนตัว',
                self._show_passport_field(),
                MultiWidgetField(
                    'birthday',
                    attrs=({'class': 'd-inline col-md-3'}
                )),
            ),
            Fieldset(
                'ข้อมูลบิดา',
                Row(
                    Div('father_prefix', css_class='col-md-2'),
                    Div('father_first_name', css_class='col-md-5'),
                    Div('father_last_name', css_class='col-md-5'),
                )
            ),
            Fieldset(
                'ข้อมูลมารดา',
                Row(
                    Div('mother_prefix', css_class='col-md-2'),
                    Div('mother_first_name', css_class='col-md-5'),
                    Div('mother_last_name', css_class='col-md-5'),
                )
            ),
            Fieldset(
                'ข้อมูลที่อยู่',
                Row(
                    Div('house_number', css_class='col-md-2'),
                    Div('village_number', css_class='col-md-2'),
                    Div('avenue', css_class='col-md-2'),
                    Div('road', css_class='col-md-6'),
                ),
                Row(
                    Div('sub_district', css_class='col-md-6'),
                    Div('district', css_class='col-md-6'),
                ),
                Row(
                    Div('province', css_class='col-md-6'),
                    Div('postal_code', css_class='col-md-6'),
                ),
                Row(
                    Div('contact_phone', css_class='col-md-6'),
                    Div('mobile_phone', css_class='col-md-6'),
                ),
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

    common_prefixes = ['โรงเรียน']
    for p in common_prefixes:
        if term.startswith(p):
            trancated_term = term[len(p):]
            schools = School.objects.filter(province=province,
                                            title__contains=trancated_term)
            results += [s.title for s in schools]
    
    return HttpResponse(json.dumps(results))


@appl_login_required        
def personal_profile(request):
    applicant = request.applicant
    profile = applicant.get_personal_profile()
    if profile is None:
        profile = PersonalProfile()
        profile.applicant = applicant

    if request.method == 'POST':
        form = PersonalProfileForm(request.POST, instance=profile)
        if form.is_valid():
            new_personal_profile = form.save(commit=False)
            new_personal_profile.applicant = applicant
            new_personal_profile.save()
            request.session['notice'] = 'จัดเก็บข้อมูลส่วนตัวเรียบร้อย'
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
            request.session['notice'] = 'จัดเก็บข้อมูลการศึกษาเรียบร้อย'
            return redirect(reverse('appl:index'))
    else:
        form = EducationForm(instance=profile)

    return render(request, 'appl/forms/education.html',
                  { 'form': form })
