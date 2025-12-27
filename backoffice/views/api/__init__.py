import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import Http404, HttpResponse
from django.contrib import messages

from backoffice.models import APIToken
from appl.models import AdmissionProject

def valid_token_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        token_auth = request.META.get("HTTP_AUTHORIZATION")
        items = token_auth.split(" ") if token_auth else []
        if len(items) == 2 and (items[0] == 'Bearer' or items[0] == 'Token'):
            token = items[1]
        else:
            token = None
        if not token or not APIToken.objects.filter(token=token).exists():
            return HttpResponse(status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@valid_token_required
def projects(request):
    projects = AdmissionProject.objects.filter(is_visible_in_backoffice=True).all()
    return HttpResponse(json.dumps({"projects": [{ 'id':p.id, 
                                                  'title': p.title } for p in projects]}), 
                        content_type="application/json")


