
"""
Кастомный бэкенд для аутентификации через университетский OAuth сервис.

Flow:
1. Получение authorization code из callback
2. Обмен code на access token
3. Получение данных пользователя через API
4. Создание/обновление пользователя в системе
"""

import requests
import logging
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from accounts.models import StudentProfile, OAuthToken

User = get_user_model()
logger = logging.getLogger(__name__)


class UniversityOAuthBackend(BaseBackend):
    """
    Кастомный бэкенд для аутентификации через университетский OAuth сервис.
    """

    def authenticate(self, request, code=None, state=None):
        """
        Основной метод аутентификации.

        Args:
            request: HttpRequest объект
            code: Authorization code от OAuth провайдера
            state: CSRF protection token

        Returns:
            User object или None
        """
        if not code:
            return None

        # Валидация state для защиты от CSRF
        if state:
            session_state = request.session.get('oauth_state')
            if not session_state or session_state != state:
                logger.warning(f"State mismatch: expected {session_state}, got {state}")
                return None

        try:

            token_data = self.get_access_token(code)
            if not token_data:
                logger.error("Failed to obtain access token")
                return None


            user_data = self.get_user_info(token_data['access_token'])
            if not user_data:
                logger.error("Failed to retrieve user info")
                return None


            user = self.get_or_create_user(user_data, token_data)


            if user:
                self.save_oauth_token(user, token_data)

            return user

        except Exception as e:
            logger.error(f"OAuth authentication error: {str(e)}")
            return None

    def get_access_token(self, code):
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code

        Returns:
            dict with token data or None
        """
        try:
            oauth_config = settings.OAUTH_PROVIDER

            payload = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': oauth_config['CLIENT_ID'],
                'client_secret': oauth_config['CLIENT_SECRET'],
                'redirect_uri': oauth_config['REDIRECT_URI'],
            }

            response = requests.post(
                oauth_config['ACCESS_TOKEN_URL'],
                data=payload,
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()
            logger.info("Successfully obtained access token")

            return {
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_in': token_data.get('expires_in', 3600),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get access token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting token: {str(e)}")
            return None

    def get_user_info(self, access_token):
        """
        Получение информации о пользователе через API.

        Args:
            access_token: Access token для авторизации

        Returns:
            dict with user data or None
        """
        try:
            oauth_config = settings.OAUTH_PROVIDER

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }

            response = requests.get(
                oauth_config['USER_INFO_URL'],
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            user_data = response.json()
            logger.info(f"Successfully retrieved user info for {user_data.get('username')}")

            return user_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get user info: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user info: {str(e)}")
            return None

    def get_or_create_user(self, user_data, token_data):
        """
        Создание или обновление пользователя на основе данных из OAuth.

        Args:
            user_data: Dictionary с данными пользователя
            token_data: Dictionary с данными токена

        Returns:
            User object или None
        """
        try:

            student_id = user_data.get('student_id') or user_data.get('id')
            username = user_data.get('username') or f"student_{student_id}"
            email = user_data.get('email', '')

            if not student_id:
                logger.error("No student ID found in user data")
                return None


            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'user_type': 'student',
                    'is_active': True,
                }
            )


            if not created:
                user.email = email or user.email
                user.first_name = user_data.get('first_name', user.first_name)
                user.last_name = user_data.get('last_name', user.last_name)
                user.save()


            if 'university' in user_data:
                user.university = user_data['university']
            if 'specialty' in user_data:
                user.specialty = user_data['specialty']
            if 'graduation_year' in user_data:
                try:
                    user.graduation_year = int(user_data['graduation_year'])
                except (ValueError, TypeError):
                    pass
            if 'phone' in user_data:
                try:
                    user.phone_number = user_data['phone']
                except:
                    pass

            user.save()

            action = "created" if created else "updated"
            logger.info(f"User {username} {action} via OAuth")

            return user

        except Exception as e:
            logger.error(f"Error creating/updating user: {str(e)}")
            return None

    def save_oauth_token(self, user, token_data):
        """
        Сохранение OAuth токенов в базу данных.

        Args:
            user: User instance
            token_data: Dictionary с данными токена
        """
        try:
            expires_at = timezone.now() + timedelta(seconds=token_data.get('expires_in', 3600))

            oauth_token, created = OAuthToken.objects.get_or_create(user=user)
            oauth_token.access_token = token_data.get('access_token')
            oauth_token.refresh_token = token_data.get('refresh_token')
            oauth_token.token_type = token_data.get('token_type', 'Bearer')
            oauth_token.expires_in = token_data.get('expires_in', 3600)
            oauth_token.expires_at = expires_at
            oauth_token.save()

            logger.info(f"OAuth token saved for user {user.username}")

        except Exception as e:
            logger.error(f"Error saving OAuth token: {str(e)}")

    def get_user(self, user_id):
        """
        Получение пользователя по ID.

        Args:
            user_id: ID пользователя

        Returns:
            User object или None
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
