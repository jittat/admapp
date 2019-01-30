from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from backoffice.views.permissions import is_super_admin, is_number_adjustment_admin

def user_login_required(view_function):
    @login_required
    def f(request, *args, **kwargs):
        request.user.is_super_admin = is_super_admin(request.user)

        if is_number_adjustment_admin(request.user):
            return redirect(reverse('backoffice:adjustment'))
        
        return view_function(request, *args, **kwargs)

    return f

def super_admin_login_required(view_function):
    @login_required
    @user_login_required
    def f(request, *args, **kwargs):
        if request.user.is_super_admin:
            return view_function(request, *args, **kwargs)
        else:
            return redirect(reverse('backoffice:index'))

    return f

def number_adjustment_login_required(view_function):
    @login_required
    def f(request, *args, **kwargs):
        request.user.is_super_admin = is_super_admin(request.user)

        if (not request.user.is_super_admin) and (not is_number_adjustment_admin(request.user)):
            return redirect(reverse('backoffice:index'))
        
        return view_function(request, *args, **kwargs)

    return f

