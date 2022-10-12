from django.contrib import admin

from .models import MajorCuptCode, CuptExportConfig


class MajorCuptCodeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'program_code', 'faculty']
    search_fields = ['program_code', 'title']

    
admin.site.register(MajorCuptCode, MajorCuptCodeAdmin)
admin.site.register(CuptExportConfig)
