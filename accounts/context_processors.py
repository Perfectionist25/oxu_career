from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def auth_context(request):
    """
    Context processor for authentication-related data
    """
    context = {}

    if request.user.is_authenticated:
        # Get unread notifications count
        unread_notifications_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by("-created_at")[:5]

        context.update(
            {
                "unread_notifications_count": unread_notifications_count,
                "recent_notifications": recent_notifications,
                "user_full_name": request.user.get_full_name(),
                "user_type": (
                    request.user.user_type
                    if hasattr(request.user, "user_type")
                    else None
                ),
            }
        )

    return context
