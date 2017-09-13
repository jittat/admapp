# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django import forms

from django.shortcuts import render, redirect

from .models import Province, School
from django.urls import reverse

# Create your views here.
class EducationForm(forms.Form):
	province_name = forms.CharField(label='จังหวัด', max_length=30)
	school_name = forms.CharField(label='ชื่อโรงเรียน', max_length=80)

	# if forms.is_valid():
	# 	province_name = f.cleaned_data['province_name']
	# 	school_name = f.cleaned_data['school_name']


def education_form(request):
	if request.method == 'POST':
		form = EducationForm(request.POST)
		if form.is_valid():
			return render(request,'form/test.html',
								{ 'province_name': form.cleaned_data['province_name'],
                                'school_name': form.cleaned_data['school_name'] })
	else :
		form = EducationForm()

	return render(request, 'form/test.html', {'form':form})


