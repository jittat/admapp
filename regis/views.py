# -*- coding: utf-8 -*-
import os, sys
from django import forms
from django.forms import ValidationError

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden

from django.contrib.auth.password_validation import validate_password

from django.conf import settings

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, ButtonHolder, Row, Div

from admapp.emails import send_registration_email, send_forget_password_email

from .validators import is_valid_national_id
from .validators import is_valid_passport_number
from .models import Applicant, LogItem

class LoginForm(forms.Form):
    national_id = forms.CharField(label='รหัสประจำตัวประชาชนหรือหมายเลขพาสปอร์ต',
                                  max_length=20)
    password = forms.CharField(label='รหัสผ่าน',
                               max_length=100,
                               widget=forms.PasswordInput)


class ForgetForm(forms.Form):
    national_id = forms.CharField(label='รหัสประจำตัวประชาชนหรือหมายเลขพาสปอร์ต',
                                  max_length=20)
    email = forms.CharField(label='อีเมลที่ลงทะเบียน',
                            max_length=100)



PASSWORD_THAI_ERROR_MESSAGES = {
    'password_entirely_numeric': 'รหัสผ่านมีแต่ตัวเลข',
    'password_too_short': 'รหัสผ่านสั้นเกินไป',
    'password_too_common': 'รหัสผ่านเป็นรหัสผ่านที่ใช้บ่อยมากเกินไป',
}

HAS_NATIONAL_ID_CHOICES = [
    ('1','เลขประจำตัวประชาชน'),
    ('0','เลขที่หนังสือเดินทาง (Passport)'),
]

class RegistrationForm(forms.Form):

    national_id = forms.CharField(label='รหัสประจำตัวประชาชน',
                                  max_length=20, 
                                  required=False)
    national_id_confirm = forms.CharField(label='ยืนยันรหัสประจำตัวประชาชน',
                                          max_length=20,
                                          required=False)

    has_national_id = forms.ChoiceField(label='วิธีการสมัคร',
                                        help_text='หากมีเลขประจำตัวประชาชน กรุณาเลือกสมัครด้วยเลขประจำตัวประชาชน',
                                        choices=HAS_NATIONAL_ID_CHOICES, 
                                        widget=forms.Select(), 
                                        initial=1)

    passport_number = forms.CharField(label='เลขที่หนังสือเดินทาง (Passport No.)', 
                                      max_length=20,
                                      required=False)
    passport_number_confirm = forms.CharField(label='ยืนยันเลขที่หนังสือเดินทาง (Passport No.)', 
                                              max_length=20,
                                              required=False)

    email = forms.EmailField(label='อีเมล',
                             help_text='กรุณากรอกอีเมลที่ใช้งานได้ เพื่อรับข้อมูลสำคัญเกี่ยวกับการสมัครเข้าศึกษาจากเรา')
    email_confirm = forms.EmailField(label='ยืนยันอีเมล')

    prefix = forms.ChoiceField(label='คำนำหน้า',
                               choices=[('นาย','นาย'),
                                        ('นางสาว','นางสาว'),
                                        ('นาง','นาง')])
    first_name = forms.CharField(label='ชื่อ',
                                 max_length=100)
    last_name = forms.CharField(label='นามสกุล',
                                max_length=200)

    password = forms.CharField(label='รหัสผ่าน',
                               max_length=100,
                               help_text='ต้องมีความยาวไม่น้อยกว่า 8 ตัวอักษร ไม่สามารถใช้เพียงตัวเลขอย่างเดียวได้',
                               widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='ยืนยันรหัสผ่าน',
                                       max_length=100,
                                       widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'ข้อมูลสำหรับการเข้าสู่ระบบ',
                'has_national_id',
                Row(
                    Div('national_id', css_class='col-md-6'),
                    Div('national_id_confirm', css_class='col-md-6'),
                ),
                Row(
                    Div('passport_number', css_class='col-md-6'),
                    Div('passport_number_confirm', css_class='col-md-6'),
                ),
                Row(
                    Div('password', css_class='col-md-6'),
                    Div('password_confirm', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'ข้อมูลพื้นฐานของผู้สมัคร',
                Row(
                    Div('prefix', css_class='col-md-2'),
                    Div('first_name', css_class='col-md-5'),
                    Div('last_name', css_class='col-md-5'),
                ),
                Row(
                    Div('email', css_class='col-md-6'),
                    Div('email_confirm', css_class='col-md-6'),
                ),
            ),
            ButtonHolder(
                Submit('submit', 'ลงทะเบียน', css_class='lbtn btn-primary')
            ),
        )

    def check_confirm_and_raise_error(self,
                                      field_name, confirm_field_name,
                                      error_message):
        if field_name in self.cleaned_data:
            if self.cleaned_data[field_name] != self.cleaned_data[confirm_field_name]:
                del self.cleaned_data[confirm_field_name]
                raise ValidationError(error_message, code='invalid')
        
    def clean_national_id(self):
        if not settings.VERIFY_NATIONAL_ID:
            return self.cleaned_data['national_id']
        
        if not is_valid_national_id(self.cleaned_data['national_id']):
            del self.cleaned_data['national_id']
            raise ValidationError('รหัสประจำตัวประชาชนผิดรูปแบบ', code='invalid')
        return self.cleaned_data['national_id']

    def clean_national_id_confirm(self):
        if ((settings.VERIFY_NATIONAL_ID) and
            (not is_valid_national_id(self.cleaned_data['national_id_confirm']))):
            del self.cleaned_data['national_id_confirm']
            raise ValidationError('รหัสประจำตัวประชาชนผิดรูปแบบ', code='invalid')

        self.check_confirm_and_raise_error('national_id', 'national_id_confirm',
                                           'รหัสประจำตัวประชาชนที่ยืนยันไม่ตรงกัน')
        return self.cleaned_data['national_id_confirm']

    def clean_passport_number(self):
        if not is_valid_passport_number(self.cleaned_data['passport_number']):
            del self.cleaned_data['passport_number']
            raise ValidationError('เลขที่หนังสือเดินทางผิดรูปแบบ', code='invalid')
        return self.cleaned_data['passport_number']

    def clean_passport_number_confirm(self):
        if not is_valid_passport_number(self.cleaned_data['passport_number_confirm']):
            del self.cleaned_data['passport_number_confirm']
            raise ValidationError('เลขที่หนังสือเดินทางผิดรูปแบบ', code='invalid')

        self.check_confirm_and_raise_error('passport_number', 'passport_number_confirm',
                                           'เลขที่หนังสือเดินทางที่ยืนยันไม่ตรงกัน')
        return self.cleaned_data['passport_number_confirm']

    def clean_email_confirm(self):
        self.check_confirm_and_raise_error('email', 'email_confirm',
                                           'อีเมลที่ยืนยันไม่ตรงกัน')
        return self.cleaned_data['email_confirm']

    def clean_password(self):
        try:
            validate_password(self.cleaned_data['password'])
        except ValidationError as errors:
            for error in errors.error_list:
                if error.code in PASSWORD_THAI_ERROR_MESSAGES:
                    error.message = PASSWORD_THAI_ERROR_MESSAGES[error.code]
            raise errors
        return self.cleaned_data['password']
    
    def clean_password_confirm(self):
        self.check_confirm_and_raise_error('password', 'password_confirm',
                                           'รหัสผ่านที่ยืนยันไม่ตรงกัน')
        return self.cleaned_data['password_confirm']


def create_applicant(form):
    applicant = Applicant(national_id=form.cleaned_data['national_id'],
                          passport_number=form.cleaned_data['passport_number'],
                          prefix=form.cleaned_data['prefix'],
                          first_name=form.cleaned_data['first_name'],
                          last_name=form.cleaned_data['last_name'],
                          email=form.cleaned_data['email'])
    applicant.set_password(form.cleaned_data['password'])
    try:
        if form.cleaned_data['has_national_id'] == '1':
            applicant.save()
            return applicant
        else:
            result = applicant.generate_random_national_id_and_save()
            if result:
                return applicant
            else:
                return None
    except:
        return None
    

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            applicant = create_applicant(form)

            LogItem.create('Registered', applicant, request)

            if applicant:
                send_registration_email(applicant)
                return render(request, 'regis/regis_result.html',
                              { 'email': form.cleaned_data['email'] })
            else:
                return render(request,'regis/registration_error.html',
                              { 'national_id': form.cleaned_data['national_id'],
                                'passport_number': form.cleaned_data['passport_number'],
                                'first_name': form.cleaned_data['first_name'] })
    else:
        form = RegistrationForm()
        
    return render(request,
                  'regis/register.html',
                  { 'form': form })


def forget(request):
    error_message = None
    update_success = False
    email = None
    
    if request.method == 'POST':
        form = ForgetForm(request.POST)
        if form.is_valid():
            national_id = form.cleaned_data['national_id']
            email = form.cleaned_data['email']
            applicant = Applicant.find_by_national_id(national_id)
            if not applicant:
                applicant = Applicant.find_by_passport_number(national_id)

            if (not applicant) or (applicant.email.upper() != email.strip().upper()):
                error_message = 'ไม่พบข้อมูลผู้สมัครที่ระบุหรืออีเมลที่ระบุไม่ถูกต้อง'
            else:
                new_password = applicant.random_password()
                applicant.save()

                LogItem.create('New password requested', applicant, request)
                
                send_forget_password_email(applicant, new_password)
                form = None
                update_success = True
                email = applicant.email
                
    else:
        form = ForgetForm()

    return render(request,
                  'regis/forget.html',
                  { 'form': form,
                    'error_message': error_message,
                    'update_success': update_success,
                    'email': email })


def login_applicant(request, applicant):
    request.session['applicant_id'] = applicant.id


def login(request):
    if request.method != 'POST':
        return HttpResponseForbidden()
    
    form = LoginForm(request.POST)
    if form.is_valid():
        national_id = form.cleaned_data['national_id']
        password = form.cleaned_data['password']

        applicant = Applicant.find_by_national_id(national_id)
        if not applicant:
            applicant = Applicant.find_by_passport_number(national_id)
            if not applicant:
                return redirect(reverse('main-index') + '?error=wrong-password')

        if ((settings.FAKE_LOGIN and settings.DEBUG)
            or applicant.check_password(password)):
            login_applicant(request, applicant)

            LogItem.create('Logged in', applicant, request)

            return redirect(reverse('appl:index'))
        else:
            LogItem.create('Failed to log in (wrong password)', applicant, request)
            
            return redirect(reverse('main-index') + '?error=wrong-password')
    else:
        return redirect(reverse('main-index') + '?error=invalid')


def logout(request):
    if 'applicant_id' in request.session:
        del request.session['applicant_id']
    return redirect(reverse('main-index'))

    
