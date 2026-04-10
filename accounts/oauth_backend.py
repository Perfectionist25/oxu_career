
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


def _pick(data, *keys):
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        if value != "":
            return value
    return None


def _normalize_gender(value):
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in {"male", "m", "erkak", "man"}:
        return "male"
    if normalized in {"female", "f", "ayol", "woman"}:
        return "female"
    return None


def _get_user_type_from_bitiruvchi(user_data):
    bitiruvchi = _pick(user_data, "bitiruvchi", "bitiruvchi_flag", "is_graduate")
    if isinstance(bitiruvchi, bool):
        return "alumni" if bitiruvchi else "student"
    if str(bitiruvchi).strip() == "1":
        return "alumni"
    return "student"


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
            external_id = _pick(user_data, "user_id", "student_id", "id")
            user_type = _get_user_type_from_bitiruvchi(user_data)
            username = _pick(user_data, "login", "preferred_username", "username")
            email = _pick(user_data, "email") or ""
            first_name = _pick(user_data, "ism", "first_name", "given_name") or ""
            last_name = _pick(user_data, "fam", "last_name", "family_name") or ""
            full_name = _pick(user_data, "full_name", "name") or f"{first_name} {last_name}".strip()
            gender = _normalize_gender(_pick(user_data, "jinsi", "gender"))

            if not external_id:
                logger.error("No external ID found in user data")
                return None

            if not username:
                username = f"student_{external_id}"

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'full_name': full_name,
                    'full_name_locked': bool(full_name),
                    'user_type': user_type,
                    'is_active': True,
                    'oauth_uid': external_id,
                    'oauth_provider': settings.OAUTH_PROVIDER.get('NAME', 'oxu') if hasattr(settings, 'OAUTH_PROVIDER') else 'oxu',
                }
            )

            profile, _ = StudentProfile.objects.get_or_create(user=user)

            updates = []
            if not created:
                if email and user.email != email:
                    user.email = email
                    updates.append('email')
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                    updates.append('first_name')
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                    updates.append('last_name')
                if full_name and user.full_name != full_name:
                    user.full_name = full_name
                    user.full_name_locked = True
                    updates.extend(['full_name', 'full_name_locked'])
                if gender and user.gender != gender:
                    user.gender = gender
                    updates.append('gender')
                if user.user_type != user_type:
                    user.user_type = user_type
                    updates.append('user_type')
                if not user.oauth_uid:
                    user.oauth_uid = external_id
                    updates.append('oauth_uid')
                if not getattr(user, 'oauth_provider', None):
                    user.oauth_provider = settings.OAUTH_PROVIDER.get('NAME', 'oxu') if hasattr(settings, 'OAUTH_PROVIDER') else 'oxu'
                    updates.append('oauth_provider')

            if created:
                user.oauth_uid = external_id
                if gender:
                    user.gender = gender
                if full_name:
                    user.full_name_locked = True
                user.oauth_provider = settings.OAUTH_PROVIDER.get('NAME', 'oxu') if hasattr(settings, 'OAUTH_PROVIDER') else 'oxu'
                user.set_unusable_password()
                updates.extend(['oauth_uid', 'oauth_provider', 'password'])

            if updates:
                user.save(update_fields=list(set(updates)))
            elif created:
                user.save()

            profile_fields = {
                'university': _pick(user_data, 'fakultet', 'university', 'oauth_university'),
                'faculty': _pick(user_data, 'fakultet', 'faculty'),
                'specialty': _pick(user_data, 'yonalish_nomi', 'specialty', 'program'),
                'specialty_code': _pick(user_data, 'yonalish_shifri'),
                'graduation_year': _pick(user_data, 'graduation_year'),
                'course_year': _pick(user_data, 'kurs'),
                'phone_number': _pick(user_data, 'phone_number', 'phone'),
                'father_name': _pick(user_data, 'otasi'),
                'skills': _pick(user_data, 'skills'),
            }

            if user_type == 'alumni':
                profile_fields['status'] = 'graduate'
            elif profile.status not in {'student', 'graduate'}:
                profile_fields['status'] = 'student'

            profile_updated = False
            for field, value in profile_fields.items():
                if value is None:
                    continue
                if field == 'graduation_year':
                    try:
                        value = int(value)
                    except (TypeError, ValueError):
                        continue
                if hasattr(profile, field) and getattr(profile, field) != value:
                    setattr(profile, field, value)
                    profile_updated = True

            if profile_updated:
                profile.save()

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
