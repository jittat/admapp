from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile
from .models import ProjectMenuConfig
from .models import APIToken

admin.site.register(Profile)

class UserProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

def make_staff(modeladmin, request, queryset):
    for user in queryset:
        user.is_staff = True
        user.save()
make_staff.short_description = 'Mark selected users as staff'

def remove_staff(modeladmin, request, queryset):
    for user in queryset:
        user.is_staff = False
        user.save()
remove_staff.short_description = 'Mark selected users as not staff'

def add_criteria_check_permission(modeladmin, request, queryset):
    for user in queryset:
        profile = user.profile
        profile.has_criteria_check_permission = True
        profile.save()
add_criteria_check_permission.short_description = 'Add criteria check permission to selected users'

def remove_criteria_check_permission(modeladmin, request, queryset):
    for user in queryset:
        profile = user.profile
        profile.has_criteria_check_permission = False
        profile.save()
remove_criteria_check_permission.short_description = 'Remove criteria check permission from selected users'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, )
    actions = [make_staff, remove_staff,
               add_criteria_check_permission, remove_criteria_check_permission]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(ProjectMenuConfig)
admin.site.register(APIToken)