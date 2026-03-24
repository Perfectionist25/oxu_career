import uuid
import requests
from datetime import timedelta
from urllib.parse import urlparse
from pathlib import Path
import base64

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import OAuthToken, StudentProfile, strip_system_generated_bio
from accounts.oauth_utils import clear_oauth_redirect_uri, get_oauth_redirect_uri


User = get_user_model()


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
        path = urlparse(source_url).path
        suffix = Path(path).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            return suffix
    return ".jpg"


def _save_avatar_from_picture(user, picture):
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
            ext = _guess_ext(
                content_type=resp.headers.get("Content-Type"),
                source_url=picture,
            )
            content = resp.content
        else:
            return False
    except Exception:
        return False

    if not content:
        return False

    filename = f"oauth_avatar_{user.pk}_{uuid.uuid4().hex[:10]}{ext}"
    user.avatar.save(filename, ContentFile(content), save=False)
    user.save(update_fields=["avatar", "updated_at"])

    try:
        profile = StudentProfile.objects.filter(user=user).first()
        if profile:
            profile.avatar = user.avatar
            profile.save(update_fields=["avatar", "updated_at"])
    except Exception:
        pass

    return True


@login_required
def oauth_user_info(request):
    user = request.user
    return JsonResponse({
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": getattr(user, "full_name", ""),
        "is_authenticated": user.is_authenticated,
    })


def oauth_callback(request):
    error = request.GET.get("error")
    if error:
        return HttpResponseBadRequest(f"OAuth error: {error}")

    code = request.GET.get("code")
    if not code:
        return HttpResponseBadRequest("No code provided")

    state = request.GET.get("state")
    session_state = request.session.get("oauth_state")
    if not state or not session_state or state != session_state:
        return HttpResponseBadRequest("Invalid state")
    request.session.pop("oauth_state", None)
    next_url = request.session.pop("oauth_next", settings.OAUTH_SUCCESS_REDIRECT)
    redirect_uri = get_oauth_redirect_uri(request)
    clear_oauth_redirect_uri(request)


    token_response = requests.post(
        settings.OAUTH_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.OAUTH_CLIENT_ID,
            "client_secret": settings.OAUTH_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
        },
        timeout=10,
    )

    if token_response.status_code != 200:
        return HttpResponseBadRequest("Failed to get access token")

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    token_type = token_data.get("token_type", "Bearer")
    expires_in = int(token_data.get("expires_in") or 3600)
    scope = token_data.get("scope")
    if not access_token:
        return HttpResponseBadRequest("No access token")


    user_response = requests.get(
        settings.OAUTH_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )

    if user_response.status_code != 200:
        return HttpResponseBadRequest("Failed to fetch user info")

    user_data = user_response.json()


    email_raw = _pick(user_data, "email")
    email = email_raw.lower() if isinstance(email_raw, str) else ""
    oauth_uid = _pick(user_data, "user_id", "sub", "id", "uid", "user_id")
    full_name = _pick(user_data, "full_name", "name") or ""
    first_name = _pick(user_data, "ism", "first_name", "given_name") or ""
    last_name = _pick(user_data, "fam", "last_name", "family_name") or ""
    oauth_login = _pick(user_data, "login", "preferred_username", "username")
    phone_number = _pick(user_data, "phone_number", "phone", "phoneNumber")
    picture = _pick(user_data, "picture", "avatar", "photo", "image")

    if oauth_uid:
        oauth_uid = str(oauth_uid).strip()

    if not email and not oauth_uid:
        return HttpResponseBadRequest("No email or uid from OAuth provider")

    provider_name = getattr(settings, "OAUTH_PROVIDER_NAME", "oxu")


    with transaction.atomic():
        user = None
        created = False

        if oauth_uid:
            user = User.objects.filter(oauth_uid=oauth_uid).first()

        if not user and email:
            user = User.objects.filter(email=email).first()

        if not user:
            base_username = oauth_login or email or f"{provider_name}_{oauth_uid or 'user'}"
            username = base_username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{uuid.uuid4().hex[:8]}"

            user = User.objects.create(
                email=email if email else "",
                username=username,
                is_active=True,
                user_type="student",
                oauth_provider=provider_name,
                oauth_uid=oauth_uid or None,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])
            created = True

        updates = []

        if not getattr(user, "oauth_provider", None):
            user.oauth_provider = provider_name
            updates.append("oauth_provider")

        if oauth_uid and not getattr(user, "oauth_uid", None):
            user.oauth_uid = oauth_uid
            updates.append("oauth_uid")

        if oauth_login and user.username != oauth_login:
            if not User.objects.filter(username=oauth_login).exclude(pk=user.pk).exists():
                user.username = oauth_login
                updates.append("username")

        if first_name and user.first_name != first_name:
            user.first_name = first_name
            updates.append("first_name")

        if last_name and user.last_name != last_name:
            user.last_name = last_name
            updates.append("last_name")

        if phone_number and str(user.phone_number or "") != phone_number:
            user.phone_number = phone_number
            updates.append("phone_number")

        if hasattr(user, "full_name") and hasattr(user, "full_name_locked"):
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                user.full_name_locked = True
                updates += ["full_name", "full_name_locked"]


        if getattr(user, "user_type", None) != "student":
            user.user_type = "student"
            updates.append("user_type")

        cleaned_bio = strip_system_generated_bio(user.bio)
        if cleaned_bio != (user.bio or "").strip():
            user.bio = cleaned_bio
            updates.append("bio")

        if updates:
            user.save(update_fields=list(set(updates)))

        student_profile, _ = StudentProfile.objects.get_or_create(user=user)
        if oauth_uid and not student_profile.student_id:
            student_profile.student_id = str(oauth_uid)
            student_profile.save(update_fields=["student_id", "updated_at"])


        oauth_token, _ = OAuthToken.objects.get_or_create(user=user)
        oauth_token.access_token = access_token
        oauth_token.refresh_token = refresh_token
        oauth_token.token_type = token_type
        oauth_token.expires_in = expires_in
        oauth_token.expires_at = timezone.now() + timedelta(seconds=expires_in)
        oauth_token.scope = scope
        oauth_token.save()

        if picture:
            _save_avatar_from_picture(user, picture)


    refresh = RefreshToken.for_user(user)
    refresh["user_type"] = "student"
    refresh["oauth_provider"] = provider_name
    access_jwt = str(refresh.access_token)
    refresh_jwt = str(refresh)

    login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
    request.session.cycle_key()
    request.session["oauth_login"] = True
    request.session["oauth_provider"] = provider_name
    request.session["oauth_access_token"] = access_token
    request.session["oauth_refresh_token"] = refresh_token
    request.session["student_access_jwt"] = access_jwt
    request.session["student_refresh_jwt"] = refresh_jwt
    request.session["student_last_activity_ts"] = int(timezone.now().timestamp())

    session_age = min(
        int(getattr(settings, "OAUTH_STUDENT_SESSION_AGE", settings.SESSION_COOKIE_AGE)),
        int(settings.SESSION_COOKIE_AGE),
    )
    request.session.set_expiry(session_age)

    try:
        from accounts.views import create_user_activity, get_client_ip
        create_user_activity(
            user,
            "login",
            "Student logged in via OAuth",
            get_client_ip(request),
            request.META.get("HTTP_USER_AGENT", ""),
        )
    except Exception:
        pass

    response = redirect(next_url)
    if getattr(settings, "OAUTH_SET_TOKEN_COOKIES", True):
        cookie_secure = getattr(settings, "SESSION_COOKIE_SECURE", False)
        same_site = getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax")
        response.set_cookie(
            getattr(settings, "OAUTH_ACCESS_COOKIE_NAME", "student_access"),
            access_jwt,
            httponly=True,
            secure=cookie_secure,
            samesite=same_site,
            max_age=int(getattr(settings, "SIMPLE_JWT", {}).get("ACCESS_TOKEN_LIFETIME", timedelta(minutes=20)).total_seconds()),
        )
        response.set_cookie(
            getattr(settings, "OAUTH_REFRESH_COOKIE_NAME", "student_refresh"),
            refresh_jwt,
            httponly=True,
            secure=cookie_secure,
            samesite=same_site,
            max_age=int(getattr(settings, "SIMPLE_JWT", {}).get("REFRESH_TOKEN_LIFETIME", timedelta(days=7)).total_seconds()),
        )

    return response
