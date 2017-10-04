from django.http import HttpResponseForbidden


def document_view(request,document_id):
    return HttpResponseForbidden()
