from django.http import HttpResponseForbidden


def document_view(request,document_id = 0):
    return HttpResponseForbidden()
