# Redis + Celery в OXU Career

## Обзор

Ваш проект использует **Celery** для асинхронного выполнения задач и **Redis** как message broker (очередь сообщений).

## Архитектура

```
Django приложение
       ↓
   Celery задача
       ↓
    Redis (очередь)
       ↓
   Celery Worker (обработчик)
       ↓
   Выполнение + сохранение результата в Redis
```

## Конфигурация (settings.py)

```python
REDIS_URL = "redis://localhost:6379/0"
CELERY_BROKER_URL = REDIS_URL           # Redis как очередь задач
CELERY_RESULT_BACKEND = REDIS_URL       # Redis как хранилище результатов
CELERY_TASK_TIME_LIMIT = 300            # Максимум 5 минут на задачу
CELERY_TASK_TRACK_STARTED = True        # Отслеживание статуса
```

## Что Celery делает в проекте

### 1. **Сжатие аватаров** (`accounts/tasks.py`)
```python
@shared_task
def compress_avatar_task(user_id):
    # Когда пользователь загружает аватар:
    # 1. Сжимает изображение до 512x512
    # 2. Преобразует в WebP (экономит трафик)
    # 3. Качество 75% для оптимальности
    # 4. При ошибке повторяет 3 раза с интервалом 30 сек
```

**Когда запускается**: При загрузке/обновлении аватара пользователя

**Зачем**: 
- Асинхронная обработка (не блокирует запрос)
- Экономия памяти сервера
- Сжатие трафика (WebP меньше чем JPG)

### 2. **Тестовые задачи** (`core/tasks.py`)
```python
ping()            # Возвращает "pong" - проверка живого Celery
debug_task()      # Проверка что Celery запущен
```

## Запуск Redis + Celery

### Вариант 1: Локально (требует установленный Redis)
```bash
# Терминал 1: Redis сервер
redis-server

# Терминал 2: Celery worker (обработчик задач)
celery -A config worker -l info

# Терминал 3: Celery beat (планировщик периодических задач)
celery -A config beat -l info
```

### Вариант 2: Docker (рекомендуется)
Добавить Redis сервис в `docker-compose.yml`:
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  restart: unless-stopped
```

## Состояние в проекте

| Компонент | Статус |
|-----------|--------|
| Redis | Установлен (requirements.txt) |
| Celery | Установлен и настроен ✓ |
| Django-Celery-Beat | Установлен для периодических задач ✓ |
| Docker Redis | ⚠️ Отсутствует в docker-compose.yml |

## Как использовать Celery для новых задач

```python
# в любом tasks.py приложения
from celery import shared_task

@shared_task(bind=True)
def my_async_task(self, param):
    # Асинхронно выполнится в worker'е
    return f"Результат: {param}"

# В view'е: запуск задачи
from myapp.tasks import my_async_task

my_async_task.delay(param_value)  # Запуск async
result = my_async_task.apply_async(args=[param_value], countdown=10)  # С задержкой
```

## Проблемы если Redis/Celery не запущен

- ❌ Аватары не будут сжиматься
- ❌ Периодические задачи не выполнятся
- ❌ Задачи будут накапливаться в памяти (потеря при перезагрузке)

## Мониторинг

```bash
# Проверить живого ли Celery
celery -A config inspect active

# Посмотреть статус воркеров
celery -A config inspect stats

# Проверить зарегистрированные задачи
celery -A config inspect registered
```
