from django.contrib import admin

from .models import User, UserGroup


# from guardian.admin import GuardedModelAdmin
# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number')

class GroupInline(admin.TabularInline):
    model = User.groups.through


# class UserGroupAdmin(GuardedModelAdmin):
#     search_fields = ['name']
#     inlines = [GroupInline, ]


# admin.site.register(UserGroup, UserGroupAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UserGroup)

