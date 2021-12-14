from rest_framework import permissions


class IsCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            return True
        return obj.created_by == request.user


class IsProviderDetail(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            return True

        return obj.business.created_by == request.user
