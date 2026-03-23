import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
import base64

import requests
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.models import (
    ADMIN_USER_TYPES,
    StudentProfile,
    EmployerProfile,
    AdminProfile,
    strip_system_generated_bio,
)
from accounts.views import create_user_activity, get_client_ip

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


def _guess_ext(content_type=None, source_url=None):
    if content_type:
        ct = content_type.lower()
        if "jpeg" in ct or "jpg" in ct:
            return ".jpg"
        if "png" in ct:
            return ".png"
        if "webp" in ct:
            return ".webp"
        if "gif" in ct:
            return ".gif"
    if source_url:
        suffix = Path(urlparse(source_url).path).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            return suffix
    return ".jpg"


def _save_user_avatar(user, picture):
    if not picture or not isinstance(picture, str):
        return False

    picture = picture.strip()
    if not picture:
        return False

    content = None
    ext = ".jpg"
    try:
        if picture.startswith("data:image/") and ";base64," in picture:
            header, b64data = picture.split(";base64,", 1)
            ext = _guess_ext(content_type=header.replace("data:", ""))
            content = base64.b64decode(b64data)
        elif picture.startswith("http://") or picture.startswith("https://"):
            resp = requests.get(picture, timeout=10)
            if resp.status_code != 200 or not resp.content:
                return False
            ext = _guess_ext(resp.headers.get("Content-Type"), picture)
            content = resp.content
    except Exception:
        return False

    if not content:
        return False

    filename = f"oauth_avatar_{user.pk}_{timezone.now().strftime('%Y%m%d%H%M%S')}{ext}"
    user.avatar.save(filename, ContentFile(content), save=False)
    user.save(update_fields=["avatar", "updated_at"])

    profile = StudentProfile.objects.filter(user=user).first()
    if profile:
        profile.avatar = user.avatar
        profile.save(update_fields=["avatar", "updated_at"])
    return True






def get_oauth_config():
    """Get OAuth configuration from settings"""
    return {
        'client_id': getattr(settings, 'OAUTH2_CLIENT_ID', ''),
        'client_secret': getattr(settings, 'OAUTH2_CLIENT_SECRET', ''),
        'base_url': getattr(settings, 'OAUTH2_BASE_URL', ''),
        'redirect_uri': getattr(settings, 'OAUTH2_REDIRECT_URI', ''),
        'authorize_url': getattr(settings, 'OAUTH2_AUTHORIZE_URL', ''),
        'token_url': getattr(settings, 'OAUTH2_TOKEN_URL', ''),
        'userinfo_url': getattr(settings, 'OAUTH2_USERINFO_URL', ''),
        'provider_name': getattr(settings, 'OAUTH2_PROVIDER_NAME', 'oxu'),
    }


def build_oauth_authorize_url(request):
    """Build OAuth authorization URL with state parameter"""
    config = get_oauth_config()

    # Generate state parameter for CSRF protection
    import secrets
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state
    request.session['oauth_redirect'] = request.GET.get('next', reverse('accounts:student_dashboard'))


    params = {
        'client_id': config['client_id'],
        'redirect_uri': config['redirect_uri'],
        'response_type': 'code',
        'scope': 'openid profile email phone',
        'state': state,

        'prompt': 'select_account',
        'access_type': 'offline',
    }

    from urllib.parse import urlencode
    return f"{config['authorize_url']}?{urlencode(params)}"






def exchange_code_for_token(code: str) -> dict:
    """
    Exchange authorization code for access token
    """
    config = get_oauth_config()

    try:
        token_url = config["token_url"]
        if not token_url.startswith("http"):
            token_url = f"{config['base_url']}{token_url}"

        response = requests.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config['redirect_uri'],
                "client_id": config['client_id'],
                "client_secret": config['client_secret'],
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Token exchange failed: {str(e)}")
        raise Exception(f"OAuth token service error: {str(e)}")


def fetch_oauth_user_info(access_token: str) -> dict:
    """
    Get user info from OAuth provider using access token
    """
    config = get_oauth_config()

    try:
        userinfo_url = config["userinfo_url"]
        if not userinfo_url.startswith("http"):
            userinfo_url = f"{config['base_url']}{userinfo_url}"

        response = requests.get(
            userinfo_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"User info fetch failed: {str(e)}")
        raise Exception(f"OAuth userinfo service error: {str(e)}")


def find_or_create_student_user(oauth_user_data: dict) -> tuple:
    """
    Find or create student user based on OAuth data
    Returns: (user, created)
    """
    external_id = _pick(oauth_user_data, "user_id", "sub", "id", "uid")
    email_raw = _pick(oauth_user_data, "email")
    email = email_raw.lower() if isinstance(email_raw, str) else ""
    username = _pick(oauth_user_data, "login", "preferred_username", "username")
    phone = _pick(oauth_user_data, "phone_number", "phone")
    first_name = _pick(oauth_user_data, "ism", "given_name", "first_name") or ""
    last_name = _pick(oauth_user_data, "fam", "family_name", "last_name") or ""
    full_name = _pick(oauth_user_data, "full_name", "name") or ""
    picture = _pick(oauth_user_data, "picture", "avatar", "photo", "image")

    if not external_id:
        raise ValueError("No external ID in OAuth response")


    user = None
    created = False

    try:
        user = User.objects.get(oauth_uid=external_id, user_type="student")
        logger.info(f"Found existing student user: {user.username}")
    except User.DoesNotExist:

        if email:
            try:
                user = User.objects.get(email=email, user_type="student")

                user.oauth_uid = external_id
                user.oauth_provider = "oxu"
                user.save(update_fields=["oauth_uid", "oauth_provider", "updated_at"])
                logger.info(f"Updated existing student user with OAuth ID: {user.username}")
            except User.DoesNotExist:
                pass
            except User.MultipleObjectsReturned:

                pass


    if not user:

        if not username or User.objects.filter(username=username).exists():
            import uuid
            username = f"student_{str(external_id)[:8]}_{uuid.uuid4().hex[:6]}"


        if email and User.objects.filter(email=email).exists():

            email = f"{email.split('@')[0]}+{external_id[:4]}@{email.split('@')[1]}"



        with transaction.atomic():
            user = User.objects.create(
                username=username,
                email=email if email else "",
                first_name=first_name,
                last_name=last_name,
                phone_number=phone,
                oauth_uid=external_id,
                oauth_provider="oxu",
                user_type="student",
                is_active=True,
                is_verified=True,
            )


            user.set_unusable_password()
            user.save()


            StudentProfile.objects.create(user=user)


            profile_fields = {
                'university': oauth_user_data.get('university'),
                'faculty': oauth_user_data.get('faculty'),
                'specialty': oauth_user_data.get('specialty'),
                'graduation_year': oauth_user_data.get('graduation_year'),
            }

            if any(profile_fields.values()):
                student_profile = StudentProfile.objects.get(user=user)
                for field, value in profile_fields.items():
                    if value and hasattr(student_profile, field):
                        setattr(student_profile, field, value)
                student_profile.save()

            created = True
            logger.info(f"Created new student user: {user.username}")

    updates = []
    if username and user.username != username and not User.objects.filter(username=username).exclude(pk=user.pk).exists():
        user.username = username
        updates.append("username")
    if first_name and user.first_name != first_name:
        user.first_name = first_name
        updates.append("first_name")
    if last_name and user.last_name != last_name:
        user.last_name = last_name
        updates.append("last_name")
    if full_name and getattr(user, "full_name", "") != full_name:
        user.full_name = full_name
        user.full_name_locked = True
        updates.extend(["full_name", "full_name_locked"])
    if phone and str(user.phone_number or "") != phone:
        user.phone_number = phone
        updates.append("phone_number")
    cleaned_bio = strip_system_generated_bio(user.bio)
    if cleaned_bio != (user.bio or "").strip():
        user.bio = cleaned_bio
        updates.append("bio")
    if updates:
        user.save(update_fields=list(set(updates)))

    if external_id:
        student_profile, _ = StudentProfile.objects.get_or_create(user=user)
        if not student_profile.student_id:
            student_profile.student_id = str(external_id)
            student_profile.save(update_fields=["student_id", "updated_at"])

    if picture:
        _save_user_avatar(user, picture)

    return user, created


def generate_jwt_tokens_for_user(user):
    """
    Generate JWT tokens manually (not through /api/token/)
    """
    refresh = RefreshToken.for_user(user)


    refresh['user_type'] = user.user_type
    refresh['username'] = user.username

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }






@require_http_methods(["GET"])
def oauth_login(request):
    """
    OAuth Login Redirect
    GET /oauth/login/

    Redirects to OAuth provider's authorization endpoint
    """
    try:
        auth_url = build_oauth_authorize_url(request)
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"OAuth login error: {str(e)}")
        return JsonResponse({
            'error': 'Failed to initiate OAuth login',
            'message': str(e)
        }, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def oauth_callback(request):
    """
    OAuth Callback Handler
    POST /oauth/callback/

    Handles authorization code exchange, user creation, and JWT issuance
    """
    try:

        code = request.data.get("code")
        state = request.data.get("state")


        if not code:
            return Response(
                {"error": "Authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not state:
            return Response(
                {"error": "State parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )


        session_state = request.session.get('oauth_state')
        if not session_state or state != session_state:
            return Response(
                {"error": "Invalid state parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )


        if 'oauth_state' in request.session:
            del request.session['oauth_state']


        try:
            token_data = exchange_code_for_token(code)
        except Exception as e:
            logger.error(f"Token exchange error: {str(e)}")
            return Response(
                {"error": "OAuth token service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        access_token = token_data.get("access_token")
        if not access_token:
            return Response(
                {"error": "No access token received from OAuth provider"},
                status=status.HTTP_400_BAD_REQUEST
            )


        try:
            oauth_user_data = fetch_oauth_user_info(access_token)
        except Exception as e:
            logger.error(f"User info fetch error: {str(e)}")
            return Response(
                {"error": "OAuth userinfo service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


        try:
            user, created = find_or_create_student_user(oauth_user_data)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"User creation error: {str(e)}")
            return Response(
                {"error": "Failed to create or find user"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


        try:
            tokens = generate_jwt_tokens_for_user(user)
        except Exception as e:
            logger.error(f"JWT generation error: {str(e)}")
            return Response(
                {"error": "Failed to generate authentication tokens"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


        try:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            create_user_activity(
                user,
                "login",
                "Student logged in via OAuth",
                ip_address,
                user_agent
            )
        except Exception as e:
            logger.warning(f"Failed to log user activity: {str(e)}")


        response_data = {
            "access": tokens['access'],
            "refresh": tokens['refresh'],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_type": user.user_type,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "oauth_provider": user.oauth_provider,
                "created": created,
            }
        }


        if user.is_student:
            try:
                profile = StudentProfile.objects.get(user=user)
                response_data['user']['profile'] = {
                    'phone_number': profile.phone_number,
                    'university': profile.university,
                    'faculty': profile.faculty,
                    'specialty': profile.specialty,
                    'graduation_year': profile.graduation_year,
                }
            except StudentProfile.DoesNotExist:
                pass

        logger.info(f"OAuth login successful for user: {user.username}")
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Unhandled error in oauth_callback: {str(e)}", exc_info=True)
        return Response(
            {"error": "Internal server error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def oauth_user_info(request):
    """
    Get authenticated user information
    GET /oauth/user-info/
    """
    user = request.user


    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "user_type": user.user_type,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "is_active": user.is_active,
        "date_joined": user.date_joined,
        "last_login": user.last_login,
        "oauth_provider": user.oauth_provider,
        "phone_number": user.phone_number,
    }


    if user.user_type == "student":
        try:
            profile = StudentProfile.objects.get(user=user)
            data.update({
                "role": "student",
                "profile": {
                    "phone_number": profile.phone_number,
                    "university": profile.university,
                    "faculty": profile.faculty,
                    "specialty": profile.specialty,
                    "graduation_year": profile.graduation_year,
                    "gpa": profile.gpa,
                    "bio": profile.bio,
                    "skills": profile.skills,
                }
            })
        except StudentProfile.DoesNotExist:
            data["profile"] = None

    elif user.user_type == "employer":
        try:
            profile = EmployerProfile.objects.get(user=user)
            data.update({
                "role": "employer",
                "profile": {
                    "company_count": profile.companies.count() if hasattr(profile, 'companies') else 0,
                    "position": profile.position,
                    "department": profile.department,
                }
            })
        except EmployerProfile.DoesNotExist:
            data["profile"] = None

    elif user.user_type in ADMIN_USER_TYPES:
        try:
            profile = AdminProfile.objects.get(user=user)
            data.update({
                "role": user.user_type,
                "profile": {
                    "can_manage_students": profile.can_manage_students,
                    "can_manage_employers": profile.can_manage_employers,
                    "can_create_employers": profile.can_create_employers,
                    "can_change_user_status": profile.can_change_user_status,
                    "can_manage_companies": profile.can_manage_companies,
                    "can_view_company_details": profile.can_view_company_details,
                    "can_verify_companies": profile.can_verify_companies,
                    "can_change_company_status": profile.can_change_company_status,
                    "can_manage_jobs": profile.can_manage_jobs,
                    "can_create_jobs": profile.can_create_jobs,
                    "can_manage_resumes": profile.can_manage_resumes,
                    "can_manage_events": profile.can_manage_events,
                    "can_view_statistics": profile.can_view_statistics,
                }
            })
        except AdminProfile.DoesNotExist:
            data["profile"] = None

    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def oauth_refresh_token(request):
    """
    Refresh JWT token
    POST /oauth/refresh/
    """
    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response(
            {"error": "Refresh token is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:

        from rest_framework_simplejwt.serializers import TokenRefreshSerializer

        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        if serializer.is_valid():
            data = serializer.validated_data
            response_payload = {
                "access": data['access'],
            }
            if "refresh" in data:
                response_payload["refresh"] = data["refresh"]
            return Response(response_payload, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return Response(
            {"error": "Failed to refresh token"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def oauth_logout(request):
    """
    Logout user (invalidate tokens on client side)
    POST /oauth/logout/
    """
    user = request.user


    try:
        ip_address = get_client_ip(request)
        create_user_activity(
            user,
            "logout",
            "User logged out",
            ip_address,
            request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception as e:
        logger.warning(f"Failed to log logout activity: {str(e)}")

    if request.user.is_authenticated:
        logout(request)

    response = Response({
        "message": "Logged out successfully"
    }, status=status.HTTP_200_OK)

    access_cookie = getattr(settings, "OAUTH_ACCESS_COOKIE_NAME", "student_access")
    refresh_cookie = getattr(settings, "OAUTH_REFRESH_COOKIE_NAME", "student_refresh")
    response.delete_cookie(access_cookie)
    response.delete_cookie(refresh_cookie)
    return response






from rest_framework.views import APIView
from rest_framework.permissions import BasePermission


class IsStudentUser(BasePermission):
    """
    Permission check for student users only
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'student'
        )


class StudentDashboardAPI(APIView):
    """
    Example: Student-only API endpoint
    """
    permission_classes = [IsAuthenticated, IsStudentUser]

    def get(self, request):

        user = request.user


        from jobs.models import JobApplication
        from cvbuilder.models import CV

        applications = JobApplication.objects.filter(user=user).count()
        cvs = CV.objects.filter(user=user).count()

        return Response({
            "message": f"Welcome, {user.full_name}!",
            "stats": {
                "applications": applications,
                "cvs": cvs,
                "profile_views": user.profile_views,
            }
        })
