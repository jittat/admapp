from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseForbidden
from django import forms
from django.contrib.auth.models import User

from backoffice.models import Profile
from backoffice.decorators import super_admin_login_required
from .permissions import is_super_admin

@super_admin_login_required
def index(request):
    users = User.objects.all()

    for u in users:
        u.is_super_admin = is_super_admin(u)
    
    return render(request,
                  'backoffice/users/index.html',
                  { 'users': users,
                  })
