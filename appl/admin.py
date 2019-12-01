from django.contrib import admin

from .models import ProjectUploadedDocument, AdmissionProject, AdmissionRound, AdmissionProjectRound, Faculty

class ProjectUploadedDocumentInline(admin.StackedInline):
    model = ProjectUploadedDocument.admission_projects.through
    can_delete = True

def make_available(modeladmin, request, queryset):
    for project in queryset:
        project.is_available = True
        project.save()
make_available.short_description = 'Mark selected project as available'
        
class AdmissionProjectAdmin(admin.ModelAdmin):
    list_display = ['title',
                    'campus',
                    'get_admission_rounds_display',
                    'max_num_selections',
                    'base_fee',
                    'is_available']
    ordering = ['id']
    actions = [make_available]
    inlines = (ProjectUploadedDocumentInline,)

class ProjectUploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'notes', 'file_prefix']

class AdmissionProjectRoundAdmin(admin.ModelAdmin):
    list_display = ['__str__',
                    'applying_deadline',
                    'is_started',
                    'payment_deadline',
                    'accepted_for_interview_result_shown',
                    'accepted_result_shown']

admin.site.register(AdmissionProject, AdmissionProjectAdmin)
admin.site.register(AdmissionRound)
admin.site.register(AdmissionProjectRound, AdmissionProjectRoundAdmin)
admin.site.register(ProjectUploadedDocument, ProjectUploadedDocumentAdmin)
admin.site.register(Faculty)
