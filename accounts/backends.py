from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework_simplejwt.authentication import JWTAuthentication

User = get_user_model()


class OAuthBackend(BaseBackend):
    """
    Бэкенд для аутентификации студентов через OAuth.
    """
    
    def authenticate(self, request, **kwargs):
        """
        Аутентификация через OAuth для студентов.
        Для employer/admin используется стандартная аутентификация.
        """
        # Этот метод будет использоваться при OAuth колбэке
        code = kwargs.get('code')
        state = kwargs.get('state')
        
        if code and state:
            # OAuth аутентификация - обрабатывается в oauth_callback view
            return None
        
        # Для остальных случаев возвращаем None
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class EmailBackend(BaseBackend):
    """
    Бэкенд для аутентификации по email.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(
                Q(email=username) | Q(username=username)
            )
            
            # Студенты не могут аутентифицироваться по паролю
            if user.user_type == 'student':
                return None
                
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class JWTStudentBackend(JWTAuthentication):
    """
    Кастомный JWT бэкенд для студентов с проверкой user_type.
    """
    
    def get_user(self, validated_token):
        """
        Получение пользователя из токена с проверкой типа.
        """
        user = super().get_user(validated_token)
        
        # Если пользователь студент и OAuth аутентификация, разрешаем доступ
        if user and user.user_type == 'student' and user.oauth_uid:
            return user
        
        # Для остальных случаев - стандартная проверка
        return user