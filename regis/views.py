from django import forms
from django.forms import ValidationError

from django.shortcuts import render

from .validators import is_valid_national_id

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
                               max_length=100)
    password_confirm = forms.CharField(label='ยืนยันรหัสผ่าน',
                                       max_length=100)

    def clean_national_id(self):
        if not is_valid_national_id(self.cleaned_data['national_id']):
            del self.cleaned_data['national_id']
            raise ValidationError('รหัสประจำตัวประชาชนผิดรูปแบบ', code='invalid')
        return self.cleaned_data['national_id']

    def check_confirm_and_raise_error(self,
                                      field_name, confirm_field_name,
                                      error_message):
        if field_name in self.cleaned_data:
            if self.cleaned_data[field_name] != self.cleaned_data[confirm_field_name]:
                del self.cleaned_data[confirm_field_name]
                raise ValidationError(error_message, code='invalid')
        
    def clean_national_id_confirm(self):
        if not is_valid_national_id(self.cleaned_data['national_id_confirm']):
            del self.cleaned_data['national_id_confirm']
            raise ValidationError('รหัสประจำตัวประชาชนผิดรูปแบบ', code='invalid')

        self.check_confirm_and_raise_error('national_id', 'national_id_confirm',
                                           'รหัสประจำตัวประชาชนที่ยืนยันไม่ตรงกัน')
        return self.cleaned_data['national_id_confirm']

    def clean_email_confirm(self):
        self.check_confirm_and_raise_error('email', 'email_confirm',
                                           'อีเมลที่ยืนยันไม่ตรงกัน')
        return self.cleaned_data['email_confirm']

    def clean_password_confirm(self):
        self.check_confirm_and_raise_error('password', 'password_confirm',
                                           'รหัสผ่านที่ยืนยันไม่ตรงกัน')
        return self.cleaned_data['password_confirm']

    
        
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            pass
    else:
        form = RegistrationForm()
        
    return render(request,
                  'regis/register.html',
                  { 'form': form })

