# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponseRedirect

from .forms import personaldataForm

def personeldata(request):
    if request.method == 'POST':
        form = personaldataForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = personaldataForm()

    return render(request, 'personaldata.html', {'form': form})
