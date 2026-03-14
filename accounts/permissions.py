from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

User = get_user_model()

class IsStudentUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'student'
        )


class IsEmployerUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'employer'
        )


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.user_type in ['admin', 'main_admin']
        )


class IsMainAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'main_admin'
        )


class ReadOnlyOrIsStudent(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return IsStudentUser().has_permission(request, view)


class StudentNoPasswordAuth(BasePermission):
    def has_permission(self, request, view):

        if request.user and request.user.is_authenticated:
            if request.user.user_type == 'student':

                return bool(request.user.oauth_uid)
        return True