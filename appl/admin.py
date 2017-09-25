from django.contrib import admin

from .models import ProjectUploadedDocument, AdmissionProject, AdmissionRound, AdmissionProjectRound

def make_available(modeladmin, request, queryset):
    for project in queryset:
        project.is_available = True
        project.save()
make_available.short_description = 'Mark selected project as available'

        
class AdmissionProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'campus', 'get_admission_rounds_display', 'is_available']
    ordering = ['id']
    actions = [make_available]
    
admin.site.register(AdmissionProject, AdmissionProjectAdmin)
admin.site.register(AdmissionRound)
admin.site.register(AdmissionProjectRound)
admin.site.register(ProjectUploadedDocument)

