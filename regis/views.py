from django import forms
from django.forms import ValidationError

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden

from django.contrib.auth.password_validation import validate_password

from django.conf import settings
 
from .validators import is_valid_national_id
from .models import Applicant

class LoginForm(forms.Form):
    national_id = forms.CharField(label='รหัสประจำตัวประชาชน',
                                  max_length=20)
    password = forms.CharField(label='รหัสผ่าน',
                               max_length=100,
                               widget=forms.PasswordInput)


class RegistrationForm(forms.Form):
    national_id = forms.CharField(label='รหัสประจำตัวประชาชน',
                                  max_length=20)
    national_id_confirm = forms.CharField(label='ยืนยันรหัสประจำตัวประชาชน',
                                          max_length=20)

    email = forms.EmailField(label='อีเมล')
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
                               help_text='ต้องมีความยาวไม่น้อยกว่า 8 ตัวอักษร ห้ามใช้แต่ตัวเลข',
                               widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='ยืนยันรหัสผ่าน',
                                       max_length=100,
                                       widget=forms.PasswordInput)

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

    def clean_email_confirm(self):
        self.check_confirm_and_raise_error('email', 'email_confirm',
                                           'อีเมลที่ยืนยันไม่ตรงกัน')
        return self.cleaned_data['email_confirm']

    def clean_password(self):
        validate_password(self.cleaned_data['password'])
        return self.cleaned_data['password']
    
    def clean_password_confirm(self):
        self.check_confirm_and_raise_error('password', 'password_confirm',
                                           'รหัสผ่านที่ยืนยันไม่ตรงกัน')
        return self.cleaned_data['password_confirm']


def create_applicant(form):
    applicant = Applicant(national_id=form.cleaned_data['national_id'],
                          prefix=form.cleaned_data['prefix'],
                          first_name=form.cleaned_data['first_name'],
                          last_name=form.cleaned_data['last_name'],
                          email=form.cleaned_data['email'])
    applicant.set_password(form.cleaned_data['password'])
    try:
        applicant.save()
        return True
    except:
        return False
    

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            if create_applicant(form):
                return redirect(reverse('main-index'))
            else:
                return render(request,'regis/registration_error.html',
                              { 'national_id': form.cleaned_data['national_id'],
                                'first_name': form.cleaned_data['first_name'] })
    else:
        form = RegistrationForm()
        
    return render(request,
                  'regis/register.html',
                  { 'form': form })

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
            return redirect(reverse('main-index') + '?error=wrong-password')

        if applicant.check_password(password):
            login_applicant(request, applicant)
            return redirect(reverse('regis:apptemp'))
        else:
            return redirect(reverse('main-index') + '?error=wrong-password')
    else:
        return redirect(reverse('main-index') + '?error=invalid')


def logout(request):
    if 'applicant_id' in request.session:
        del request.session['applicant_id']
    return redirect(reverse('main-index'))

    
def apptemp(request):
    if 'applicant_id' not in request.session:
        return redirect(reverse('main-index') + '?error=no-login')

    applicant_id = request.session['applicant_id']
    applicant = get_object_or_404(Applicant,pk=applicant_id)
    
    return render(request,
                  'regis/apptemp.html',
                  { 'applicant': applicant })

        
        
