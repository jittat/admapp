from django.shortcuts import render

from regis.views import LoginForm

def index(request):
    login_form = LoginForm()

    if 'error' in request.GET:
        error_message = request.GET['error']
    else:
        error_message = None
    
    return render(request,
                  'main/index.html',
                  { 'login_form': login_form,
                    'error_message': error_message })


