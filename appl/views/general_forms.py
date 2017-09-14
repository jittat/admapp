# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render, redirect
from django import forms

from appl.models import Province, School
from django.urls import reverse

class EducationForm(forms.Form):
    province_name = forms.CharField(label='จังหวัด', max_length=30)
    school_name = forms.CharField(label='ชื่อโรงเรียน', max_length=80)

    
def education(request):
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            return render(request,'form/test.html',
			  { 'province_name': form.cleaned_data['province_name'],
                            'school_name': form.cleaned_data['school_name'] })
    else:
        form = EducationForm()
            
    return render(request, 'appl/forms/education.html', {'form':form})


