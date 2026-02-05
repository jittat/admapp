# -*- coding: utf-8 -*-
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, ButtonHolder, Row, Div
from django import forms
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from admapp.emails import send_registration_email, send_forget_password_email
from .decorators import appl_login_required
from .models import Applicant, LogItem
from .validators import is_valid_national_id
from .validators import is_valid_passport_number


class LoginForm(forms.Form):
    national_id = forms.CharField(label=_('รหัสประจำตัวประชาชนหรือหมายเลขพาสปอร์ต'),
                                  max_length=20)
    password = forms.CharField(label=_('รหัสผ่าน'),
                               max_length=100,
                               widget=forms.PasswordInput)


class ForgetForm(forms.Form):
    national_id = forms.CharField(label=_('รหัสประจำตัวประชาชนหรือหมายเลขพาสปอร์ต'),
                                  max_length=20)
    email = forms.CharField(label=_('อีเมลที่ลงทะเบียน'),
                            max_length=100)



PASSWORD_THAI_ERROR_MESSAGES = {
    'password_entirely_numeric': _('รหัสผ่านมีแต่ตัวเลข'),
    'password_too_short': _('รหัสผ่านสั้นเกินไป'),
    'password_too_common': _('รหัสผ่านเป็นรหัสผ่านที่ใช้บ่อยมากเกินไป'),
}

HAS_NATIONAL_ID_CHOICES = [
    ('1',_('มีรหัสประจำตัวประชาชน')),
    ('0',_('ไม่มีรหัสประจำตัวประชาชน (ใช้เลขที่หนังสือเดินทางในการสมัคร)')),
]

class RegistrationForm(forms.Form):

    has_national_id = forms.ChoiceField(label=_('ผู้สมัครที่มีรหัสประจำตัวประชาชน ต้องสมัครด้วยรหัสประจำตัวประชาชนเท่านั้น'),
                                        help_text=_('หากเคยสมัครแล้วแต่ไม่สามารถเข้าสู่ระบบได้ กรุณากดขอรหัสผ่านใหม่'),
                                        choices=HAS_NATIONAL_ID_CHOICES, 
                                        widget=forms.Select(), 
                                        initial=1)

    national_id = forms.CharField(label=_('รหัสประจำตัวประชาชน'),
                                  max_length=20, 
                                  required=False)
    national_id_confirm = forms.CharField(label=_('ยืนยันรหัสประจำตัวประชาชน'),
                                          max_length=20,
                                          required=False)

    passport_number = forms.CharField(label=_('เลขที่หนังสือเดินทาง (Passport No.)'), 
                                      max_length=20,
                                      required=False)
    passport_number_confirm = forms.CharField(label=_('ยืนยันเลขที่หนังสือเดินทาง (Passport No.)'), 
                                              max_length=20,
                                              required=False)

    email = forms.EmailField(label=_('อีเมล'),
                             help_text=_('กรุณากรอกอีเมลที่ใช้งานได้ เพื่อรับข้อมูลสำคัญเกี่ยวกับการสมัครเข้าศึกษาจากเรา'))
    email_confirm = forms.EmailField(label=_('ยืนยันอีเมล'))

    prefix = forms.ChoiceField(label=_('คำนำหน้า'),
                               choices=[('นาย',_('นาย')),
                                        ('นางสาว',_('นางสาว')),
                                        ('นาง',_('นาง'))])
    first_name = forms.CharField(label=_('ชื่อ'),
                                 max_length=100)
    last_name = forms.CharField(label=_('นามสกุล'),
                                max_length=200)

    password = forms.CharField(label=_('รหัสผ่าน'),
                               max_length=100,
                               help_text=_('ต้องมีความยาวไม่น้อยกว่า 8 ตัวอักษร ไม่สามารถประกอบขึ้นจากตัวเลขเพียงอย่างเดียวได้'),
                               widget=forms.PasswordInput)
    password_confirm = forms.CharField(label=_('ยืนยันรหัสผ่าน'),
                                       max_length=100,
                                       widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('ข้อมูลสำหรับการเข้าสู่ระบบ'),
                Row(
                    Div('national_id', css_class='col-md-6'),
                    Div('national_id_confirm', css_class='col-md-6'),
                ),
                'has_national_id',
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
                _('ข้อมูลพื้นฐานของผู้สมัคร'),
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
                Submit('submit', _('ลงทะเบียน'), css_class='lbtn btn-primary')
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

        if 'has_national_id' not in self.cleaned_data:
            raise ValidationError('invalid_submission',code='form_error')

        if self.cleaned_data['has_national_id'] == '0':
            return ''
        
        if not is_valid_national_id(self.cleaned_data['national_id']):
            del self.cleaned_data['national_id']
            raise ValidationError(_('รหัสประจำตัวประชาชนผิดรูปแบบ'), code='invalid')
        return self.cleaned_data['national_id']

    def clean_national_id_confirm(self):
        if 'has_national_id' not in self.cleaned_data:
            raise ValidationError('invalid_submission',code='form_error')

        if self.cleaned_data['has_national_id'] == '0':
            return ''
        
        if ((settings.VERIFY_NATIONAL_ID) and
            (not is_valid_national_id(self.cleaned_data['national_id_confirm']))):
            del self.cleaned_data['national_id_confirm']
            raise ValidationError(_('รหัสประจำตัวประชาชนผิดรูปแบบ'), code='invalid')

        self.check_confirm_and_raise_error('national_id', 'national_id_confirm',
                                           _('รหัสประจำตัวประชาชนที่ยืนยันไม่ตรงกัน'))
        return self.cleaned_data['national_id_confirm']

    def clean_passport_number(self):
        if 'has_national_id' not in self.cleaned_data:
            raise ValidationError('invalid_submission',code='form_error')

        if self.cleaned_data['has_national_id'] == '1':
            return ''
        
        if not is_valid_passport_number(self.cleaned_data['passport_number']):
            del self.cleaned_data['passport_number']
            raise ValidationError(_('เลขที่หนังสือเดินทางผิดรูปแบบ'), code='invalid')
        return self.cleaned_data['passport_number']

    def clean_passport_number_confirm(self):
        if 'has_national_id' not in self.cleaned_data:
            raise ValidationError('invalid_submission',code='form_error')

        if self.cleaned_data['has_national_id'] == '1':
            return ''
        
        if not is_valid_passport_number(self.cleaned_data['passport_number_confirm']):
            del self.cleaned_data['passport_number_confirm']
            raise ValidationError(_('เลขที่หนังสือเดินทางผิดรูปแบบ'), code='invalid')

        self.check_confirm_and_raise_error('passport_number', 'passport_number_confirm',
                                           _('เลขที่หนังสือเดินทางที่ยืนยันไม่ตรงกัน'))
        return self.cleaned_data['passport_number_confirm']

    def clean_email_confirm(self):
        self.check_confirm_and_raise_error('email', 'email_confirm',
                                           _('อีเมลที่ยืนยันไม่ตรงกัน'))
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
                                           _('รหัสผ่านที่ยืนยันไม่ตรงกัน'))
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
    
SERVER_ERROR500_HTML="""<!doctype html>
<html lang="en">
<head>
  <title>Server Error (500)</title>
</head>
<body>
  <h1>Server Error (500)</h1><p></p>
</body>
</html>
"""

class RuntimeErrorNoLogging(RuntimeError):
    pass

def register(request):
    registration_enabled = settings.REGISTRATION_ENABLED
    if not registration_enabled:
        return HttpResponseForbidden()
    
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
            form_submission_error = False
            for field, errors in form.errors.as_data().items():
                for e in errors:
                    if e.code == 'form_error':
                        form_submission_error = True

            if form_submission_error:
                LogItem.create('Registration form error', None, request)

                from random import random
                is_sending_email = (random() < register.sending_mail_prob)   # only send 5% of error
                if is_sending_email:
                    return HttpResponseServerError(SERVER_ERROR500_HTML)
                else:
                    raise RuntimeErrorNoLogging('Registration form invalid submission')
    else:
        form = RegistrationForm()
        
    return render(request,
                  'regis/register.html',
                  { 'form': form })

register.sending_mail_prob = 0.05

def check_recent_forget_logitem(applicant):
    recent_log_item = LogItem.get_applicant_latest_log(applicant,
                                                       'New password')
    if not recent_log_item:
        return True

    from datetime import datetime, timedelta

    return recent_log_item.created_at + timedelta(minutes=5) <= datetime.now()


def forget(request):
    error_message = None
    update_success = False
    email = None

    if request.method == 'POST':
        form = ForgetForm(request.POST)
        if form.is_valid():
            national_id = form.cleaned_data['national_id']
            email = form.cleaned_data['email']

            if is_valid_national_id(national_id) or is_valid_passport_number(national_id):
                applicant = Applicant.find_by_national_id(national_id)
                if not applicant:
                    applicant = Applicant.find_by_passport_number(national_id)
            else:
                applicant = None    

            if (not applicant) or (applicant.email.upper() != email.strip().upper()):
                error_message = _('ไม่พบข้อมูลผู้สมัครที่ระบุหรืออีเมลที่ระบุไม่ถูกต้อง')
            elif not check_recent_forget_logitem(applicant):
                error_message = 'ผู้สมัครได้ขอรหัสผ่านใหม่ไปแล้ว กรุณารออย่างน้อย 5 นาที ก่อนจะขอรหัสผ่านใหม่อีกครั้ง อีเมลรหัสผ่านอาจจะถูกส่งเข้าไปที่กล่องขยะ กรุณาอย่าลืมตรวจสอบ'
            else:
                new_password = applicant.random_password()
                applicant.save()

                LogItem.create('New password requested (' + new_password + ')', applicant, request)
                
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

        if is_valid_national_id(national_id) or is_valid_passport_number(national_id):
            applicant = Applicant.find_by_national_id(national_id)
            if not applicant:
                applicant = Applicant.find_by_passport_number(national_id)
        else:
            applicant = None    
        
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


def check_cupt_confirmation_available(request, national_id):
    applicant = get_object_or_404(Applicant,national_id=national_id)
    if hasattr(applicant,'cupt_confirmation'):
        return HttpResponse('OK')
    else:
        return HttpResponse('WAIT')

@appl_login_required    
def reset_cupt_confirmation(request):
    from datetime import datetime, timedelta
    
    applicant = request.applicant
    if hasattr(applicant,'cupt_confirmation'):
        confirmation = applicant.cupt_confirmation
        wait_start_time = datetime.now() - timedelta(minutes=10)
        if confirmation.updated_at < wait_start_time:
            confirmation.delete()
        else:
            request.session['notice'] = 'ยังไม่สามารถตรวจสอบการลงทะเบียนหรือสิทธิ์การสมัครใหม่ได้ กรุณารอ 10 นาที'
            
    return redirect('appl:index')

@appl_login_required    
def save_applicant_log(request):
    applicant = request.applicant

    if applicant.national_id != request.GET.get('nat',''):
        return HttpResponseForbidden()

    if LogItem.generate_log_key(applicant) != request.GET.get('key',''):
        return HttpResponseForbidden()

    msg = 'appllog:' + request.GET.get('msg','')
    LogItem.create(msg, applicant, request)
    return HttpResponse('OK')
    
