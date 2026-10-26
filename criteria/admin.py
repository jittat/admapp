from django.contrib import admin

from .models import MajorCuptCode, CuptExportConfig, CuptExportLog, CuptExportAdditionalProjectRule, CuptExportCustomProject


class MajorCuptCodeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'program_code', 'faculty']
    search_fields = ['program_code', 'title']


class CuptExportAdditionalProjectRuleAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'admission_project', 'rule_json']


class CuptExportConfigAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'admission_project']
    search_fields = ['title']
    ordering = ['admission_project', 'title']


admin.site.register(MajorCuptCode, MajorCuptCodeAdmin)
admin.site.register(CuptExportConfig, CuptExportConfigAdmin)
admin.site.register(CuptExportLog)
admin.site.register(CuptExportCustomProject)
admin.site.register(CuptExportAdditionalProjectRule,
                    CuptExportAdditionalProjectRuleAdmin)
