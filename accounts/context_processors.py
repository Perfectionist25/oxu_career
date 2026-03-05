from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def auth_context(request):
    """
    Context processor for authentication-related data
    """
    context = {}
    user = getattr(request, "user", None)

    if user and user.is_authenticated:

        unread_notifications_count = Notification.objects.filter(
            user=user, is_read=False
        ).count()
        recent_notifications = Notification.objects.filter(
            user=user
        ).order_by("-created_at")[:5]

        context.update(
            {
                "unread_notifications_count": unread_notifications_count,
                "recent_notifications": recent_notifications,
                "user_full_name": user.get_full_name(),
                "user_type": (
                    user.user_type
                    if hasattr(user, "user_type")
                    else None
                ),
            }
        )

    return context
