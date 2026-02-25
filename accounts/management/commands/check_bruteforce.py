# accounts/management/commands/check_bruteforce.py
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone

class Command(BaseCommand):
    help = 'Показать текущие блокировки и попытки входа'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить все блокировки и счетчики',
        )
        parser.add_argument(
            '--ip',
            type=str,
            help='Показать информацию по конкретному IP',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_all_blocks()
            return
        
        if options['ip']:
            self.show_ip_info(options['ip'])
            return
        
        self.show_all_blocks()

    def clear_all_blocks(self):
        """Очистить все блокировки"""
        keys = self._iter_cache_keys()
        
        block_keys = [k for k in keys if 'blocked' in k or 'attempts' in k]
        
        for key in block_keys:
            cache.delete(key)
        
        self.stdout.write(
            self.style.SUCCESS(f'Удалено {len(block_keys)} блокировок и счетчиков')
        )

    def show_ip_info(self, ip_address):
        """Показать информацию по IP"""
        ip_attempts = cache.get(f'login_attempts_ip_{ip_address}', 0)
        ip_blocked = cache.get(f'ip_blocked_{ip_address}')
        
        self.stdout.write(f'IP адрес: {ip_address}')
        self.stdout.write(f'Количество попыток: {ip_attempts}')
        self.stdout.write(f'Заблокирован: {"Да" if ip_blocked else "Нет"}')
        
        if ip_blocked:
            ttl = self._remaining_seconds(ip_blocked)
            self.stdout.write(f'Блокировка истекает через: {ttl} секунд')

    def show_all_blocks(self):
        """Показать все текущие блокировки"""
        keys = self._iter_cache_keys()
        
        ip_blocks = []
        user_blocks = []
        ip_attempts = []
        user_attempts = []
        
        for key in keys:
            if key.startswith('ip_blocked_'):
                ip = key.replace('ip_blocked_', '')
                ttl = self._remaining_seconds(cache.get(key))
                ip_blocks.append((ip, ttl))
            elif key.startswith('user_blocked_'):
                user = key.replace('user_blocked_', '')
                ttl = self._remaining_seconds(cache.get(key))
                user_blocks.append((user, ttl))
            elif key.startswith('login_attempts_ip_'):
                ip = key.replace('login_attempts_ip_', '')
                attempts = cache.get(key, 0)
                ip_attempts.append((ip, attempts))
            elif key.startswith('login_attempts_user_'):
                user = key.replace('login_attempts_user_', '')
                attempts = cache.get(key, 0)
                user_attempts.append((user, attempts))
        
        self.stdout.write(self.style.SUCCESS('=== ТЕКУЩИЕ БЛОКИРОВКИ ==='))
        
        if ip_blocks:
            self.stdout.write('\nЗаблокированные IP:')
            for ip, ttl in ip_blocks:
                self.stdout.write(f'  {ip}: {ttl} секунд до разблокировки')
        else:
            self.stdout.write('\nНет заблокированных IP')
        
        if user_blocks:
            self.stdout.write('\nЗаблокированные пользователи:')
            for user, ttl in user_blocks:
                self.stdout.write(f'  {user}: {ttl} секунд до разблокировки')
        else:
            self.stdout.write('\nНет заблокированных пользователей')
        
        if ip_attempts:
            self.stdout.write('\nАктивные счетчики попыток (IP):')
            for ip, attempts in ip_attempts:
                self.stdout.write(f'  {ip}: {attempts} попыток')
        
        if user_attempts:
            self.stdout.write('\nАктивные счетчики попыток (Пользователи):')
            for user, attempts in user_attempts:
                self.stdout.write(f'  {user}: {attempts} попыток')

    def _iter_cache_keys(self):
        # LocMemCache only. For other backends, key listing may not be available.
        internal = getattr(cache, "_cache", None)
        if internal is None:
            self.stdout.write(self.style.WARNING(
                "Текущий cache backend не поддерживает просмотр ключей. "
                "Используйте --ip для точечной проверки."
            ))
            return []
        return list(internal.keys())

    def _remaining_seconds(self, raw_block_value):
        if isinstance(raw_block_value, (int, float)):
            return max(0, int(raw_block_value) - int(timezone.now().timestamp()))
        if isinstance(raw_block_value, bool) and raw_block_value:
            return 900
        return 0
