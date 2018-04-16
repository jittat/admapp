import json

from django.shortcuts import render, redirect
from django import forms
from django.forms import ModelForm
from django.http import HttpResponse
from django.urls import reverse

from django.utils.translation import ugettext_lazy as _
from django.utils.text import format_lazy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, MultiWidgetField, Div, Row, HTML

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
        self.helper.layout = Layout(
            'education_level',
            Row(
                Div(
                    HTML(format_lazy('<small>{0}</small>', _('ถ้าจบจากโรงเรียนนานาชาติหรือต่างประเทศและไม่มี GPA สามารถกรอกเป็น 0 ได้ และสามารถเลือกแผนการเรียนเป็นไม่ระบุได้'))),
                    css_class='col-md-12 form-text mb5',
                ),
                style="display: none;"
            ),
            Row(
                Div('education_plan', css_class='col-md-6'),
                Div('gpa', css_class='col-md-6'),
                style="display: none;"
            ),
            Row(
                Div(
                    HTML(format_lazy('<b>{0}</b>',_('ข้อมูลโรงเรียน'))),
                    css_class='col-md-12',
                ),
                style="display: none;"
            ),
            Row(
                Div(
                    HTML(format_lazy('<small>{0}</small>', _('ในกรณีที่สมัครโครงการช้างเผือก สามารถเลือกให้แสดงเฉพาะโรงเรียนที่เข้าโครงการได้ โดยกดปุ่มตอนท้าย'))),
                    css_class='col-md-12 form-text mb5',
                ),
                style="display: none;"
            ),
            #Row(
            #    Div('province', css_class='col-md-6'),
            #    Div('school_title', css_class='col-md-6'),
            #),
            Row(
                Div('province', css_class='col-md-6', style="display: none;"),
                Div('school_title', css_class='col-md-12'),
                style="display: none;"
            ),
            Row(
                Div(
                    HTML('<input id="wh_school_check_id" type="checkbox" /> &nbsp;'),
                    HTML(_('แสดงรายการเฉพาะโรงเรียนในโครงการช้างเผือก')),
                    css_class='col-md-12 mb5',
                ),
                style="display: none;"
            ),
            ButtonHolder(
                Submit('submit', _('จัดเก็บ'), css_class='btn btn-primary')
            )
        )


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
            'prefix_english': _('คำนำหน้า'),
            'first_name_english': _('ชื่อต้น'),
            'middle_name_english': _('ชื่อกลาง (ถ้ามี)'),
            'last_name_english': _('นามสกุล'),
            'father_prefix': _('คำนำหน้า'),
            'father_first_name': _('ชื่อต้น'),
            'father_last_name': _('นามสกุล'),
            'mother_prefix': _('คำนำหน้า'),
            'mother_first_name': _('ชื่อต้น'),
            'mother_last_name': _('นามสกุล'),
        }
        exclude = ['applicant']
        widgets = {
            'birthday': ThaiSelectDateWidget(years=range(1920,2010))
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
                _('ข้อมูลผู้สมัครภาษาอังกฤษ'),
                Row(
                    Div('prefix_english', css_class='col-md-2'),
                    Div('first_name_english', css_class='col-md-3'),
                    Div('middle_name_english', css_class='col-md-3'),
                    Div('last_name_english', css_class='col-md-4'),
                ),
            ),
            Fieldset(
                _('ข้อมูลส่วนตัว'),
                self._show_passport_field(),
                MultiWidgetField(
                    'birthday',
                    attrs=({'class': 'd-inline col-md-3'}
                )),
            ),
            Fieldset(
                _('ข้อมูลบิดา (ภาษาไทย)'),
                Row(
                    Div('father_prefix', css_class='col-md-2'),
                    Div('father_first_name', css_class='col-md-5'),
                    Div('father_last_name', css_class='col-md-5'),
                ),
                style="display: none;",
            ),
            Fieldset(
                _('ข้อมูลมารดา (ภาษาไทย)'),
                Row(
                    Div('mother_prefix', css_class='col-md-2'),
                    Div('mother_first_name', css_class='col-md-5'),
                    Div('mother_last_name', css_class='col-md-5'),
                ),
                style="display: none;",
            ),
            Fieldset(
                _('ข้อมูลที่อยู่'),
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
                Submit('submit', _('จัดเก็บ'), css_class='btn btn-primary')
            )
        )


@appl_login_required
def ajax_school_search(request):
    province = request.GET['province']

    if province == '':
        return HttpResponse(json.dumps([]))
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
    print(results)
    return HttpResponse(json.dumps(results))


@appl_login_required
def ajax_topschool_list(request):
    province = request.GET['province']
    if province == '':
        return HttpResponse(json.dumps([]))

    schools = School.objects.filter(province=province,
                                    topschool__isnull=False)
    results = [s.title for s in schools]

    return HttpResponse(json.dumps(results))


@appl_login_required
def personal_profile(request):
    applicant = request.applicant
    profile = applicant.get_personal_profile()
    if profile is None:
        instruction_step = 2
        profile = PersonalProfile()
        profile.applicant = applicant
        profile.father_prefix = '--'
        profile.father_first_name = 'ไม่ต้องกรอก'
        profile.father_last_name = 'ไม่ต้องกรอก'
        profile.mother_prefix = '--'
        profile.mother_first_name = 'ไม่ต้องกรอก'
        profile.mother_last_name = 'ไม่ต้องกรอก'
    else:
        instruction_step = None

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

    return render(request,
                  'appl/forms/personal.html',
                  { 'form': form,
                    'instruction_step': instruction_step,
                    'applicant': applicant,
                  })


@appl_login_required
def education_profile(request):
    applicant = request.applicant
    profile = applicant.get_educational_profile()
    if profile is None:
        instruction_step = 3
    else:
        instruction_step = None

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
        if not profile:
            form = EducationForm(initial={ 'gpa': 0.0,
                                           'province': Province.objects.first(),
                                           'school_title': 'ไม่ระบุ',
                                           'education_plan': 5 })
        else:
            form = EducationForm(instance=profile)

    return render(request,
                  'appl/forms/education.html',
                  { 'form': form,
                    'instruction_step': instruction_step,
                    'applicant': applicant,
                  })
