from django.contrib import admin

from .models import ProjectUploadedDocument, AdmissionProject

admin.site.register(AdmissionProject)
admin.site.register(ProjectUploadedDocument)


