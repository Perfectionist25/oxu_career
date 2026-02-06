from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

User = get_user_model()


class IsStudentUser(BasePermission):
    """
    Разрешает доступ только студентам.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'student'
        )


class IsEmployerUser(BasePermission):
    """
    Разрешает доступ только работодателям.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'employer'
        )


class IsAdminUser(BasePermission):
    """
    Разрешает доступ только администраторам.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type in ['admin', 'main_admin']
        )


class IsMainAdminUser(BasePermission):
    """
    Разрешает доступ только главному администратору.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'main_admin'
        )


class ReadOnlyOrIsStudent(BasePermission):
    """
    Разрешает чтение всем, но запись только студентам.
    """
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return IsStudentUser().has_permission(request, view)


class StudentNoPasswordAuth(BasePermission):
    """
    Специальное разрешение для студентов - они не используют пароли.
    """
    
    def has_permission(self, request, view):
        # Для студентов запрещаем стандартную аутентификацию по паролю
        if request.user and request.user.is_authenticated:
            if request.user.user_type == 'student':
                # Студенты должны иметь oauth_uid
                return bool(request.user.oauth_uid)
        return True