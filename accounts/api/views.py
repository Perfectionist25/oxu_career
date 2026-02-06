# accounts/api/views.py
import requests

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.db import transaction

User = get_user_model()


@login_required
def oauth_user_info(request):
    user = request.user
    return JsonResponse({
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": getattr(user, "full_name", ""),  # если добавил поле
        "is_authenticated": user.is_authenticated,
    })


def oauth_callback(request):
    error = request.GET.get("error")
    if error:
        return HttpResponseBadRequest(f"OAuth error: {error}")

    code = request.GET.get("code")
    if not code:
        return HttpResponseBadRequest("No code provided")

    # 1) Exchange code -> token
    token_response = requests.post(
        settings.OAUTH_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.OAUTH_CLIENT_ID,
            "client_secret": settings.OAUTH_CLIENT_SECRET,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
        },
        timeout=10,
    )

    if token_response.status_code != 200:
        return HttpResponseBadRequest("Failed to get access token")

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        return HttpResponseBadRequest("No access token")

    # 2) Get user info
    user_response = requests.get(
        settings.OAUTH_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )

    if user_response.status_code != 200:
        return HttpResponseBadRequest("Failed to fetch user info")

    user_data = user_response.json()

    # --- ВАЖНО: тут подстрой под реальные ключи твоего провайдера ---
    # Обычно: id/sub/uid + name/full_name + email
    email = (user_data.get("email") or "").strip().lower()
    oauth_uid = (
        user_data.get("sub")
        or user_data.get("id")
        or user_data.get("uid")
        or user_data.get("user_id")
    )
    full_name = (user_data.get("full_name") or user_data.get("name") or "").strip()

    if not email and not oauth_uid:
        return HttpResponseBadRequest("No email or uid from OAuth provider")

    provider_name = getattr(settings, "OAUTH_PROVIDER_NAME", "hemis")  # можешь задать в settings.py

    # 3) Get or create user
    # Сначала пытаемся найти по oauth_uid (надёжнее, чем email)
    with transaction.atomic():
        user = None
        created = False

        if oauth_uid:
            user = User.objects.filter(oauth_uid=str(oauth_uid)).first()

        if not user and email:
            user = User.objects.filter(email=email).first()

        if not user:
            # Создаём нового студента
            username = email if email else f"{provider_name}_{oauth_uid}"
            user = User.objects.create(
                email=email if email else "",
                username=username,
                is_active=True,
                user_type="student",  # чтобы создался StudentProfile через сигнал
                oauth_provider=provider_name,
                oauth_uid=str(oauth_uid) if oauth_uid else None,
            )
            created = True

        # Обновляем provider/uid, если не заполнены (НЕ трогаем, если уже есть)
        updates = []

        if not getattr(user, "oauth_provider", None):
            user.oauth_provider = provider_name
            updates.append("oauth_provider")

        if oauth_uid and not getattr(user, "oauth_uid", None):
            user.oauth_uid = str(oauth_uid)
            updates.append("oauth_uid")

        # Главное: ФИО пишем ТОЛЬКО 1 раз и сразу lock
        # - если created -> ставим
        # - если не created -> ставим только если пусто и не залочено
        if hasattr(user, "full_name") and hasattr(user, "full_name_locked"):
            if created:
                if full_name:
                    user.full_name = full_name
                    user.full_name_locked = True
                    updates += ["full_name", "full_name_locked"]
            else:
                if full_name and (not user.full_name) and (not user.full_name_locked):
                    user.full_name = full_name
                    user.full_name_locked = True
                    updates += ["full_name", "full_name_locked"]

        # На всякий: если существовал как guest — переключим в student (по твоим требованиям)
        if getattr(user, "user_type", None) != "student":
            user.user_type = "student"
            updates.append("user_type")

        if updates:
            user.save(update_fields=list(set(updates)))

    # 4) Login & redirect
    login(request, user)
    return redirect(settings.OAUTH_SUCCESS_REDIRECT)
