from rest_framework import permissions



OWNER_PERMISSIONS = [("group_admin", "Admin access in group"), ]


class IsCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user


class IsListCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user_list = obj.tagged_users.all()
        for g in obj.user_groups.all():
            user_list = user_list | g.users.all()
        user_list = user_list.distinct()
        if request.method == 'GET' and request.user in user_list:
            return True
        return obj.created_by == request.user


class IsInCheckList(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        user_list = obj.note.tagged_users.all()

        for g in obj.note.user_groups.all():
            user_list = user_list | g.users.all()

        user_list = user_list.distinct()

        if request.user in user_list:
            return True
        else:
            return False

class IsCheckListCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.note.created_by == request.user
