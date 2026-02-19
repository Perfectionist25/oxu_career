import json
import logging
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.models import StudentProfile, EmployerProfile, AdminProfile
from accounts.views import create_user_activity, get_client_ip

User = get_user_model()
logger = logging.getLogger(__name__)


# ==========================
# OAUTH CONFIGURATION
# ==========================

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
    
    # Build authorization URL
    params = {
        'client_id': config['client_id'],
        'redirect_uri': config['redirect_uri'],
        'response_type': 'code',
        'scope': 'openid profile email phone',
        'state': state,
        # Add optional parameters
        'prompt': 'select_account',
        'access_type': 'offline',
    }
    
    from urllib.parse import urlencode
    return f"{config['authorize_url']}?{urlencode(params)}"


# ==========================
# OAUTH HELPERS
# ==========================

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
    external_id = oauth_user_data.get("sub") or oauth_user_data.get("id")
    email = oauth_user_data.get("email", "").strip().lower()
    username = oauth_user_data.get("preferred_username") or oauth_user_data.get("username")
    phone = oauth_user_data.get("phone_number")
    
    if not external_id:
        raise ValueError("No external ID in OAuth response")
    
    # Try to find existing user by oauth_uid
    user = None
    created = False
    
    try:
        user = User.objects.get(oauth_uid=external_id, user_type="student")
        logger.info(f"Found existing student user: {user.username}")
    except User.DoesNotExist:
        # Try to find by email (but only if email exists and user is student)
        if email:
            try:
                user = User.objects.get(email=email, user_type="student")
                # Update oauth_uid for existing student
                user.oauth_uid = external_id
                user.oauth_provider = "oxu"
                user.save()
                logger.info(f"Updated existing student user with OAuth ID: {user.username}")
            except User.DoesNotExist:
                pass
            except User.MultipleObjectsReturned:
                # Handle duplicate emails
                pass
    
    # Create new user if not found
    if not user:
        # Generate unique username if not provided
        if not username or User.objects.filter(username=username).exists():
            import uuid
            username = f"student_{external_id[:8]}_{uuid.uuid4().hex[:6]}"
        
        # Handle duplicate email
        if email and User.objects.filter(email=email).exists():
            # Append suffix to email
            email = f"{email.split('@')[0]}+{external_id[:4]}@{email.split('@')[1]}"
        
        # Extract names from OAuth data
        first_name = oauth_user_data.get("given_name") or oauth_user_data.get("first_name", "")
        last_name = oauth_user_data.get("family_name") or oauth_user_data.get("last_name", "")
        
        # Create user with transaction for safety
        with transaction.atomic():
            user = User.objects.create(
                username=username,
                email=email if email else None,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone,
                oauth_uid=external_id,
                oauth_provider="oxu",
                user_type="student",
                is_active=True,
                is_verified=True,
            )
            
            # Set unusable password for students
            user.set_unusable_password()
            user.save()
            
            # Create student profile
            StudentProfile.objects.create(user=user)
            
            # Update profile with additional info if available
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
    
    return user, created


def generate_jwt_tokens_for_user(user):
    """
    Generate JWT tokens manually (not through /api/token/)
    """
    refresh = RefreshToken.for_user(user)
    
    # Add custom claims if needed
    refresh['user_type'] = user.user_type
    refresh['username'] = user.username
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ==========================
# OAUTH VIEWS
# ==========================

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
        # Get parameters
        code = request.data.get("code")
        state = request.data.get("state")
        
        # Validate input
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
        
        # Verify state parameter
        session_state = request.session.get('oauth_state')
        if not session_state or state != session_state:
            return Response(
                {"error": "Invalid state parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clear state from session
        if 'oauth_state' in request.session:
            del request.session['oauth_state']
        
        # 1️⃣ Exchange code for token
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
        
        # 2️⃣ Get user info from OAuth provider
        try:
            oauth_user_data = fetch_oauth_user_info(access_token)
        except Exception as e:
            logger.error(f"User info fetch error: {str(e)}")
            return Response(
                {"error": "OAuth userinfo service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # 3️⃣ Find or create student user
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
        
        # 4️⃣ Generate JWT tokens MANUALLY
        try:
            tokens = generate_jwt_tokens_for_user(user)
        except Exception as e:
            logger.error(f"JWT generation error: {str(e)}")
            return Response(
                {"error": "Failed to generate authentication tokens"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 5️⃣ Log user activity
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
        
        # 6️⃣ Prepare response data
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
        
        # Add profile info for students
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
    
    # Build response data
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
    
    # Add role-specific information
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
    
    elif user.user_type in ["admin", "main_admin"]:
        try:
            profile = AdminProfile.objects.get(user=user)
            data.update({
                "role": user.user_type,
                "profile": {
                    "can_manage_students": profile.can_manage_students,
                    "can_manage_employers": profile.can_manage_employers,
                    "can_manage_companies": profile.can_manage_companies,
                    "can_manage_jobs": profile.can_manage_jobs,
                    "can_manage_resumes": profile.can_manage_resumes,
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
        # Use SimpleJWT's TokenRefreshView logic
        from rest_framework_simplejwt.serializers import TokenRefreshSerializer
        
        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        if serializer.is_valid():
            data = serializer.validated_data
            return Response({
                "access": data['access'],
            }, status=status.HTTP_200_OK)
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
    
    # Log the activity
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
    
    # Note: In SimpleJWT, tokens are stateless.
    # To invalidate on server side, you'd need token blacklisting
    # For now, we just return success - client should delete tokens
    
    return Response({
        "message": "Logged out successfully"
    }, status=status.HTTP_200_OK)


# ==========================
# STUDENT-ONLY API VIEWS (EXAMPLE)
# ==========================

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
        # This will only be accessible to authenticated students
        user = request.user
        
        # Example: Get student statistics
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
