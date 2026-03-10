
from django.conf import settings
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin
from django.apps import apps
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta
import json
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


class NotificationMiddleware(MiddlewareMixin):
    def process_template_response(self, request, response):
        """Добавляем уведомления в контекст шаблона"""
        if hasattr(response, 'context_data') and request.user.is_authenticated:
            try:

                Notification = apps.get_model('accounts', 'Notification')


                unread_count = Notification.objects.filter(
                    user=request.user,
                    is_read=False
                ).count()


                recent_notifications = Notification.objects.filter(
                    user=request.user
                ).order_by('-created_at')[:5]

                if response.context_data is None:
                    response.context_data = {}

                response.context_data['unread_notifications_count'] = unread_count
                response.context_data['recent_notifications'] = recent_notifications

            except (LookupError, Exception) as e:

                if response.context_data is None:
                    response.context_data = {}

                response.context_data['unread_notifications_count'] = 0
                response.context_data['recent_notifications'] = []

        return response


class StudentSessionTimeoutMiddleware(MiddlewareMixin):
    """
    Enforces inactivity timeout for student sessions.
    Timeout defaults to OAUTH_STUDENT_SESSION_AGE (seconds), which is tied
    to ACCESS_TOKEN_LIFETIME by default.
    """

    EXCLUDED_PATH_PREFIXES = (
        "/static/",
        "/media/",
        "/accounts/login/",
        "/accounts/logout/",
        "/accounts/oauth/",
        "/admin/",
    )

    def process_request(self, request):
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        if getattr(request.user, "user_type", None) != "student":
            return None

        path = request.path or ""
        if any(path.startswith(prefix) for prefix in self.EXCLUDED_PATH_PREFIXES):
            return None

        timeout_seconds = int(
            getattr(settings, "OAUTH_STUDENT_SESSION_AGE", 20 * 60)
        )
        if timeout_seconds <= 0:
            return None

        now_ts = int(timezone.now().timestamp())
        last_activity = request.session.get("student_last_activity_ts")

        if last_activity is not None and (now_ts - int(last_activity)) > timeout_seconds:
            logout(request)
            request.session.flush()
            response = redirect("accounts:login")

            if getattr(settings, "OAUTH_SET_TOKEN_COOKIES", True):
                secure = getattr(settings, "SESSION_COOKIE_SECURE", False)
                samesite = getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax")
                response.delete_cookie(
                    getattr(settings, "OAUTH_ACCESS_COOKIE_NAME", "student_access"),
                    samesite=samesite,
                    secure=secure,
                )
                response.delete_cookie(
                    getattr(settings, "OAUTH_REFRESH_COOKIE_NAME", "student_refresh"),
                    samesite=samesite,
                    secure=secure,
                )
            return response

        # Do not treat background API/AJAX polling as user activity.
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        if not is_ajax and not path.startswith("/api/"):
            request.session["student_last_activity_ts"] = now_ts

        return None


class BruteForceProtectionMiddleware(MiddlewareMixin):
    """
    Middleware для защиты от брутфорс-атак.
    Проверяет все запросы на наличие блокировок.
    """

    MAX_ATTEMPTS = int(getattr(settings, "BRUTEFORCE_MAX_ATTEMPTS", 10))
    ATTEMPT_WINDOW_SECONDS = int(getattr(settings, "BRUTEFORCE_ATTEMPT_WINDOW_SECONDS", 300))
    BLOCK_SECONDS = int(getattr(settings, "BRUTEFORCE_BLOCK_SECONDS", 900))
    WARNING_THRESHOLD = int(getattr(settings, "BRUTEFORCE_WARNING_THRESHOLD", 5))

    def __init__(self, get_response):
        self.get_response = get_response

        self.protected_paths = [
            '/admin/login/',
            '/accounts/admin-login/',
            '/accounts/employer-login/',
            '/accounts/login/',
            '/accounts/api/token/',
        ]


        self.excluded_paths = [
            '/accounts/admin/create-employer/',
            '/accounts/admin/create-admin/',
            '/accounts/admin/create-admin-account/',
            '/media/',
            '/static/',
            '/api/',
        ]

    @classmethod
    def _now_ts(cls):
        return int(timezone.now().timestamp())

    @classmethod
    def _attempts_ip_key(cls, ip_address):
        return f'login_attempts_ip_{ip_address}'

    @classmethod
    def _attempts_user_key(cls, username):
        return f'login_attempts_user_{username}'

    @classmethod
    def _blocked_ip_key(cls, ip_address):
        return f'ip_blocked_{ip_address}'

    @classmethod
    def _blocked_user_key(cls, username):
        return f'user_blocked_{username}'

    @classmethod
    def _remaining_seconds_from_value(cls, value):
        if value is None:
            return 0

        if isinstance(value, (int, float)):
            return max(0, int(value) - cls._now_ts())
        # Legacy boolean format from old implementation
        if isinstance(value, bool) and value:
            return cls.BLOCK_SECONDS
        return 0

    @classmethod
    def get_block_status(cls, ip_address, username=None):
        ip_remaining = cls._remaining_seconds_from_value(cache.get(cls._blocked_ip_key(ip_address)))
        user_remaining = 0
        if username:
            user_remaining = cls._remaining_seconds_from_value(cache.get(cls._blocked_user_key(username)))

        remaining_seconds = max(ip_remaining, user_remaining)
        if remaining_seconds <= 0:
            return {
                "is_blocked": False,
                "reason": None,
                "remaining_seconds": 0,
                "blocked_until": None,
            }

        reason = "ip_blocked" if ip_remaining >= user_remaining else "user_blocked"
        blocked_until = timezone.now() + timedelta(seconds=remaining_seconds)
        return {
            "is_blocked": True,
            "reason": reason,
            "remaining_seconds": remaining_seconds,
            "blocked_until": blocked_until,
        }

    @classmethod
    def _build_context(cls, ip_address, username=None, reason="blocked", remaining_seconds=None):
        remaining_seconds = remaining_seconds or cls.BLOCK_SECONDS
        blocked_until = timezone.now() + timedelta(seconds=remaining_seconds)
        remaining_minutes = max(1, (remaining_seconds + 59) // 60)
        return {
            'ip_address': ip_address,
            'username': username,
            'block_time': f'{remaining_minutes} минут',
            'remaining_seconds': remaining_seconds,
            'blocked_until': blocked_until,
            'current_time': timezone.now(),
            'reason': reason,
        }

    @classmethod
    def blocked_response(cls, request, ip_address, username=None, reason="blocked", remaining_seconds=None):
        context = cls._build_context(
            ip_address=ip_address,
            username=username,
            reason=reason,
            remaining_seconds=remaining_seconds,
        )


        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'error': f"Слишком много попыток входа. Попробуйте через {context['block_time']}.",
                'blocked_until': context['blocked_until'].isoformat(),
                'reason': reason,
            }, status=429)

        return render(request, 'accounts/too_many_requests.html', context, status=429)

    def __call__(self, request):

        if any(request.path.startswith(path) for path in self.excluded_paths):
            return self.get_response(request)


        if request.method == "POST" and any(request.path.startswith(path) for path in self.protected_paths):
            ip_address = self._get_client_ip(request)



            username = self._extract_username(request)
            status = self.get_block_status(ip_address, username)
            if status["is_blocked"]:
                return self.blocked_response(
                    request,
                    ip_address=ip_address,
                    username=username,
                    reason=status["reason"],
                    remaining_seconds=status["remaining_seconds"],
                )

        return self.get_response(request)

    def _get_client_ip(self, request):
        """Получение реального IP адреса клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _extract_username(self, request):
        """Извлекаем username из form-data или JSON тела запроса."""
        username = request.POST.get('username', '').strip()
        if username:
            return username

        if 'application/json' in (request.content_type or ''):
            try:
                payload = json.loads((request.body or b'{}').decode('utf-8'))
                return str(payload.get('username', '')).strip()
            except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
                return ""
        return ""

    @staticmethod
    def record_failed_attempt(ip_address, username=None):
        """Запись неудачной попытки входа (статический метод для использования в views)."""
        now_ts = BruteForceProtectionMiddleware._now_ts()
        ip_attempts_key = BruteForceProtectionMiddleware._attempts_ip_key(ip_address)

        attempts_ip = int(cache.get(ip_attempts_key, 0)) + 1
        cache.set(
            ip_attempts_key,
            attempts_ip,
            BruteForceProtectionMiddleware.ATTEMPT_WINDOW_SECONDS
        )

        attempts_user = 0
        if username:
            user_attempts_key = BruteForceProtectionMiddleware._attempts_user_key(username)
            attempts_user = int(cache.get(user_attempts_key, 0)) + 1
            cache.set(
                user_attempts_key,
                attempts_user,
                BruteForceProtectionMiddleware.ATTEMPT_WINDOW_SECONDS
            )

        current_attempts = max(attempts_ip, attempts_user)
        is_blocked = current_attempts >= BruteForceProtectionMiddleware.MAX_ATTEMPTS

        warning_message = None
        if is_blocked:
            blocked_until_ts = now_ts + BruteForceProtectionMiddleware.BLOCK_SECONDS
            cache.set(
                BruteForceProtectionMiddleware._blocked_ip_key(ip_address),
                blocked_until_ts,
                BruteForceProtectionMiddleware.BLOCK_SECONDS,
            )
            if username:
                cache.set(
                    BruteForceProtectionMiddleware._blocked_user_key(username),
                    blocked_until_ts,
                    BruteForceProtectionMiddleware.BLOCK_SECONDS,
                )
            remaining_seconds = BruteForceProtectionMiddleware.BLOCK_SECONDS
            logger.warning(
                "Bruteforce block triggered: ip=%s username=%s attempts=%s block_seconds=%s",
                ip_address, username, current_attempts, remaining_seconds
            )
            warning_message = "Превышено максимальное количество попыток. Доступ временно заблокирован."
            return {
                "allowed": False,
                "warning_message": warning_message,
                "remaining_attempts": 0,
                "remaining_seconds": remaining_seconds,
            }

        remaining_attempts = max(0, BruteForceProtectionMiddleware.MAX_ATTEMPTS - current_attempts)
        if current_attempts >= BruteForceProtectionMiddleware.WARNING_THRESHOLD:
            warning_message = f"Внимание: осталось {remaining_attempts} попыток до блокировки."

        return {
            "allowed": True,
            "warning_message": warning_message,
            "remaining_attempts": remaining_attempts,
            "remaining_seconds": 0,
        }

    @staticmethod
    def clear_attempts(ip_address, username=None):
        """Очистка счетчиков при успешном входе"""
        cache.delete(BruteForceProtectionMiddleware._attempts_ip_key(ip_address))
        cache.delete(BruteForceProtectionMiddleware._blocked_ip_key(ip_address))

        if username:
            cache.delete(BruteForceProtectionMiddleware._attempts_user_key(username))
            cache.delete(BruteForceProtectionMiddleware._blocked_user_key(username))

        logger.info(f"Очистка счетчиков: IP={ip_address}, User={username}")
