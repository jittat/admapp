from django.contrib.auth.models import User
from django.shortcuts import render

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

                    'any_major': u.profile.ANY_MAJOR,
                  })
