from rest_framework import permissions

from note.models import Note
from note.task.models import Task
from user.models import UserGroup


class IsGroupAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        # "note.group_admin" is defined in Owner model.
        permission_name = "user.group_admin"
        if isinstance(obj, UserGroup):
            user_group = obj
            return user.has_perm(permission_name, user_group)
        elif isinstance(obj, Note) | isinstance(obj, Task):
            ug_queryset = obj.user_groups
            user_groups = user.user_groups.filter(id__in=ug_queryset.values_list('id'))
            for user_group in user_groups:
                if user.has_perm(permission_name, user_group):
                    return True
        return False


class IsAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.group_admin == request.user

class IsUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user=request.user
        return obj==user