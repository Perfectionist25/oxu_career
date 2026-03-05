
import time
import sys
from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Команда ожидания БД для Windows"""

    def handle(self, *args, **options):
        self.stdout.write('Ожидание подключения к базе данных...')
        max_retries = 30
        retry_delay = 2

        for i in range(max_retries):
            try:
                self.stdout.write(f'Попытка подключения {i + 1}/{max_retries}...')
                connection = connections['default']
                connection.ensure_connection()

                self.stdout.write(self.style.SUCCESS('✓ База данных доступна!'))
                return
            except OperationalError as e:
                self.stdout.write(self.style.WARNING(f'Ошибка: {e}'))
                if i < max_retries - 1:
                    time.sleep(retry_delay)

        self.stdout.write(self.style.ERROR('✗ Не удалось подключиться к БД'))
        sys.exit(1)