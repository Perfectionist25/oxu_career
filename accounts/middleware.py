# accounts/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.apps import apps
from django.core.cache import cache
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


class NotificationMiddleware(MiddlewareMixin):
    def process_template_response(self, request, response):
        """Добавляем уведомления в контекст шаблона"""
        if hasattr(response, 'context_data') and request.user.is_authenticated:
            try:
                # Получаем модель динамически
                Notification = apps.get_model('accounts', 'Notification')
                
                # Добавляем количество непрочитанных уведомлений в контекст
                unread_count = Notification.objects.filter(
                    user=request.user,
                    is_read=False
                ).count()
                
                # Последние 5 непрочитанных уведомлений
                recent_notifications = Notification.objects.filter(
                    user=request.user
                ).order_by('-created_at')[:5]
                
                if response.context_data is None:
                    response.context_data = {}
                
                response.context_data['unread_notifications_count'] = unread_count
                response.context_data['recent_notifications'] = recent_notifications
                
            except (LookupError, Exception) as e:
                # Если модель не найдена или произошла ошибка БД
                if response.context_data is None:
                    response.context_data = {}
                
                response.context_data['unread_notifications_count'] = 0
                response.context_data['recent_notifications'] = []
        
        return response


class BruteForceProtectionMiddleware(MiddlewareMixin):
    """
    Middleware для защиты от брутфорс-атак.
    Проверяет все запросы на наличие блокировок.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Пути, которые должны проверяться
        self.protected_paths = [
            '/accounts/admin/login/',
            '/accounts/employer/login/', 
            '/accounts/student/login/',
            '/accounts/hemis/login/',
            '/accounts/temp-student-login/',
        ]
        
        # Пути, которые НЕ должны проверяться
        self.excluded_paths = [
            '/accounts/admin/create-employer/',
            '/accounts/admin/create-admin/',
            '/accounts/admin/create-admin-account/',
            '/admin/',  # Django admin
            '/media/',  # Медиа файлы
            '/static/',  # Статические файлы
            '/api/',  # API endpoints (если есть)
        ]
    
    def __call__(self, request):
        # Проверяем, не исключен ли текущий путь
        if any(request.path.startswith(path) for path in self.excluded_paths):
            return self.get_response(request)
        
        # Проверяем только POST запросы на защищенные пути
        if request.method == "POST" and any(request.path.startswith(path) for path in self.protected_paths):
            ip_address = self._get_client_ip(request)
            
            # Проверка блокировки по IP
            if self._is_ip_blocked(ip_address):
                return self._blocked_response(request, ip_address, reason="ip_blocked")
            
            # Проверка блокировки по пользователю (если есть username)
            if request.POST.get('username'):
                username = request.POST.get('username', '').strip()
                if self._is_user_blocked(username):
                    return self._blocked_response(request, ip_address, username, reason="user_blocked")
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        """Получение реального IP адреса клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_ip_blocked(self, ip_address):
        """Проверка, заблокирован ли IP"""
        block_key = f'ip_blocked_{ip_address}'
        return cache.get(block_key) is not None
    
    def _is_user_blocked(self, username):
        """Проверка, заблокирован ли пользователь"""
        if not username:
            return False
        block_key = f'user_blocked_{username}'
        return cache.get(block_key) is not None
    
    def _blocked_response(self, request, ip_address, username=None, reason="blocked"):
        """Ответ при блокировке"""
        # Получаем оставшееся время блокировки
        if reason == "ip_blocked":
            ttl = cache.ttl(f'ip_blocked_{ip_address}')
        elif reason == "user_blocked" and username:
            ttl = cache.ttl(f'user_blocked_{username}')
        else:
            ttl = 900  # 15 минут по умолчанию
        
        remaining_minutes = max(1, ttl // 60) if ttl else 15
        
        # Если это AJAX запрос
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'error': f'Слишком много попыток входа. Попробуйте через {remaining_minutes} минут.',
                'blocked_until': (timezone.now() + timedelta(minutes=remaining_minutes)).isoformat(),
                'reason': reason
            }, status=429)
        
        # Если обычный запрос
        context = {
            'ip_address': ip_address,
            'username': username,
            'block_time': f'{remaining_minutes} минут',
            'current_time': timezone.now(),
            'reason': reason,
        }
        
        return render(request, 'accounts/too_many_requests.html', context, status=429)
    
    @staticmethod
    def record_failed_attempt(ip_address, username=None):
        """Запись неудачной попытки входа (статический метод для использования в views)"""
        from django.core.cache import cache
        from datetime import timedelta
        
        # Ключи для счетчиков
        ip_attempts_key = f'login_attempts_ip_{ip_address}'
        user_attempts_key = f'login_attempts_user_{username}' if username else None
        
        # Увеличиваем счетчик для IP
        attempts_ip = cache.get(ip_attempts_key, 0) + 1
        cache.set(ip_attempts_key, attempts_ip, 300)  # 5 минут
        
        # Увеличиваем счетчик для пользователя (если есть)
        if username and user_attempts_key:
            attempts_user = cache.get(user_attempts_key, 0) + 1
            cache.set(user_attempts_key, attempts_user, 300)
        
        # Проверяем, не превышен ли лимит
        max_attempts = 10
        if attempts_ip >= max_attempts or (username and attempts_user >= max_attempts):
            # Блокируем IP
            cache.set(f'ip_blocked_{ip_address}', True, 900)  # 15 минут
            
            # Блокируем пользователя (если есть)
            if username:
                cache.set(f'user_blocked_{username}', True, 900)
            
            logger.warning(f"Блокировка: IP={ip_address}, User={username}, Attempts={attempts_ip}")
            return False, f"Превышено максимальное количество попыток. Блокировка на 15 минут."
        
        # Проверяем предупреждение
        warning_threshold = 5
        if attempts_ip >= warning_threshold or (username and attempts_user >= warning_threshold):
            remaining = max_attempts - max(attempts_ip, attempts_user if username else 0)
            return True, f"Внимание: осталось {remaining} попыток до блокировки."
        
        return True, None
    
    @staticmethod
    def clear_attempts(ip_address, username=None):
        """Очистка счетчиков при успешном входе"""
        from django.core.cache import cache
        
        # Удаляем счетчики
        cache.delete(f'login_attempts_ip_{ip_address}')
        cache.delete(f'ip_blocked_{ip_address}')
        
        if username:
            cache.delete(f'login_attempts_user_{username}')
            cache.delete(f'user_blocked_{username}')
        
        logger.info(f"Очистка счетчиков: IP={ip_address}, User={username}")