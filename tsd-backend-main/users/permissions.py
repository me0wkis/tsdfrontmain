import re
from django.conf import settings
from rest_framework import permissions


class IsManager(permissions.BasePermission):
    """
    Разрешает доступ только менеджерам.
    """

    def has_permission(self, request, view):
        print(f"\n[DEBUG PERM] Checking permissions")
        print(f"[DEBUG PERM] Request user: {request.user}")
        print(f"[DEBUG PERM] User type: {type(request.user)}")

        # Вместо проверки is_authenticated, проверяем наличие пользователя
        if not request.user:
            print("[DEBUG PERM] No user in request")
            return False

        # Проверяем, является ли это объектом Users
        from .models import Users
        if not isinstance(request.user, Users):
            print(f"[DEBUG PERM] User is not Users instance, it's {type(request.user)}")
            return False

        print(f"[DEBUG PERM] User alias: {request.user.alias}")
        print(f"[DEBUG PERM] User job_title: {request.user.job_title}")

        # Проверяем is_manager
        is_manager = False

        # Сначала из токена
        if hasattr(request.user, '_is_manager_from_token'):
            is_manager = request.user._is_manager_from_token
            print(f"[DEBUG PERM] Using _is_manager_from_token: {is_manager}")

        # Или из property
        elif hasattr(request.user, 'is_manager'):
            is_manager = request.user.is_manager
            print(f"[DEBUG PERM] Using model is_manager property: {is_manager}")

        print(f"[DEBUG PERM] Final is_manager: {is_manager}")
        return bool(is_manager)


class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return IsManager().has_permission(request, view)


class IsOwnerOrManager(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user or IsManager().has_permission(request, view)
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user or IsManager().has_permission(request, view)
        return IsManager().has_permission(request, view)