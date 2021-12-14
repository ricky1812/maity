from rest_framework import permissions


class IsServiceCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            return True
        return obj.business.created_by == request.user
