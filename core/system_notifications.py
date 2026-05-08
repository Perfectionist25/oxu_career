from __future__ import annotations

from collections.abc import Iterable

from django.utils import timezone

from .models import SystemNotification, UserNotificationDismissal


ANONYMOUS_DISMISSED_NOTIFICATIONS_SESSION_KEY = "dismissed_system_notification_ids"


def _normalize_notification_ids(notification_ids: Iterable[int | str] | None) -> list[int]:
    normalized_ids: list[int] = []

    for notification_id in notification_ids or []:
        try:
            normalized_value = int(notification_id)
        except (TypeError, ValueError):
            continue

        if normalized_value not in normalized_ids:
            normalized_ids.append(normalized_value)

    return normalized_ids


def get_anonymous_dismissed_notification_ids(request) -> list[int]:
    if request is None:
        return []

    return _normalize_notification_ids(
        request.session.get(ANONYMOUS_DISMISSED_NOTIFICATIONS_SESSION_KEY, [])
    )


def add_anonymous_dismissed_notification_id(request, notification_id: int) -> None:
    dismissed_ids = get_anonymous_dismissed_notification_ids(request)

    if notification_id in dismissed_ids:
        return

    dismissed_ids.append(notification_id)
    request.session[ANONYMOUS_DISMISSED_NOTIFICATIONS_SESSION_KEY] = dismissed_ids
    request.session.modified = True


def get_current_system_notifications_queryset():
    now = timezone.now()
    return SystemNotification.objects.filter(
        is_active=True,
        start_at__lte=now,
        end_at__gte=now,
    ).order_by("-start_at", "-created_at")


def get_visible_system_notifications(request):
    queryset = get_current_system_notifications_queryset().select_related("created_by")

    if request is None:
        return queryset

    anonymous_dismissed_ids = get_anonymous_dismissed_notification_ids(request)
    if anonymous_dismissed_ids:
        queryset = queryset.exclude(pk__in=anonymous_dismissed_ids)

    return queryset
