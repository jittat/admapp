from django.contrib import admin

from .models import ProjectUploadedDocument, AdmissionProject, AdmissionRound, AdmissionProjectRound, Faculty
from .models import School, Province

class ProjectUploadedDocumentInline(admin.StackedInline):
    model = ProjectUploadedDocument.admission_projects.through
    can_delete = True

def make_available(modeladmin, request, queryset):
    for project in queryset:
        project.is_available = True
        project.save()
make_available.short_description = 'Mark selected project as available'
        
def make_visible(modeladmin, request, queryset):
    for project in queryset:
        project.is_visible_in_backoffice = True
        project.save()
make_visible.short_description = 'Mark selected project as visible in backoffice'

def enable_criteria_edit(modeladmin, request, queryset):
    for project in queryset:
        project.is_criteria_edit_allowed = True
        project.save()
enable_criteria_edit.short_description = 'Enable criteria edit for selected projects'

def disable_criteria_edit(modeladmin, request, queryset):
    for project in queryset:
        project.is_criteria_edit_allowed = False
        project.save()
disable_criteria_edit.short_description = 'Disable criteria edit for selected projects'

def enable_additional_admission_form_edit(modeladmin, request, queryset):
    for project in queryset:
        project.is_additional_admission_form_edit_allowed = True
        project.save()
enable_additional_admission_form_edit.short_description = 'Enable additional admission form edit for selected projects'

def disable_additional_admission_form_edit(modeladmin, request, queryset):
    for project in queryset:
        project.is_additional_admission_form_edit_allowed = False
        project.save()
disable_additional_admission_form_edit.short_description = 'Disable additional admission form edit for selected projects'

def make_project_round_started(modeladmin, request, queryset):
    for project in queryset:
        project.is_started = True
        project.save()
make_project_round_started.short_description = 'Mark selected project rounds as started'
        
def make_project_round_stopped(modeladmin, request, queryset):
    for project in queryset:
        project.is_started = False
        project.save()
make_project_round_stopped.short_description = 'Mark selected project rounds as not started'
        
class AdmissionProjectAdmin(admin.ModelAdmin):
    list_display = ['title',
                    'campus',
                    'get_admission_rounds_display',
                    'max_num_selections',
                    'base_fee',
                    'is_available',
                    'is_visible_in_backoffice',
                    'custom_interview_start_date',
                    'admission_student_type',]
    ordering = ['id']
    actions = [
        make_available, 
        make_visible,
        enable_criteria_edit,
        disable_criteria_edit,
        enable_additional_admission_form_edit,
        disable_additional_admission_form_edit,
    ]
    inlines = (ProjectUploadedDocumentInline,)

class ProjectUploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'notes', 'file_prefix', 'is_required', 'requirement_key']

class AdmissionProjectRoundAdmin(admin.ModelAdmin):
    list_display = ['__str__',
                    'applying_deadline',
                    'is_started',
                    'payment_deadline',
                    'accepted_for_interview_result_shown',
                    'accepted_result_shown']
    actions = [make_project_round_started,
               make_project_round_stopped]

class SchoolAdmin(admin.ModelAdmin):
    list_display = ['code', 'title']
    search_fields = ['title','code']
    
admin.site.register(AdmissionProject, AdmissionProjectAdmin)
admin.site.register(AdmissionRound)
admin.site.register(AdmissionProjectRound, AdmissionProjectRoundAdmin)
admin.site.register(ProjectUploadedDocument, ProjectUploadedDocumentAdmin)
admin.site.register(Faculty)

admin.site.register(School, SchoolAdmin)
admin.site.register(Province)
