from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import SystemNotification, UserNotificationDismissal
from .system_notifications import ANONYMOUS_DISMISSED_NOTIFICATIONS_SESSION_KEY


User = get_user_model()


class SystemNotificationTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.visible_notification = SystemNotification.objects.create(
            message_ru="Важное тестовое уведомление",
            message_uz="",
            message_en="Important testing notice",
            start_at=now - timedelta(hours=1),
            end_at=now + timedelta(hours=1),
            is_active=True,
        )
        self.future_notification = SystemNotification.objects.create(
            message_ru="Будущее уведомление",
            message_uz="Kelajakdagi bildirishnoma",
            message_en="Future notice",
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=2),
            is_active=True,
        )
        self.expired_notification = SystemNotification.objects.create(
            message_ru="Просроченное уведомление",
            message_uz="Eskirgan bildirishnoma",
            message_en="Expired notice",
            start_at=now - timedelta(days=2),
            end_at=now - timedelta(days=1),
            is_active=True,
        )
        self.inactive_notification = SystemNotification.objects.create(
            message_ru="Неактивное уведомление",
            message_uz="Nofaol bildirishnoma",
            message_en="Inactive notice",
            start_at=now - timedelta(hours=1),
            end_at=now + timedelta(hours=1),
            is_active=False,
        )

    def test_home_shows_only_current_notifications_with_language_fallback(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "uz"

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Важное тестовое уведомление")
        self.assertNotContains(response, "Будущее уведомление")
        self.assertNotContains(response, "Просроченное уведомление")
        self.assertNotContains(response, "Неактивное уведомление")

    def test_home_uses_current_language_when_translation_exists(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Important testing notice")
        self.assertNotContains(response, "Важное тестовое уведомление")

    def test_authenticated_dismissal_is_saved_and_hides_notification(self):
        user = User.objects.create_user(
            username="student-user",
            password="strong-pass-123",
            user_type="student",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("core:dismiss_system_notification", args=[self.visible_notification.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            UserNotificationDismissal.objects.filter(
                user=user,
                notification=self.visible_notification,
            ).exists()
        )

        home_response = self.client.get(reverse("core:home"))
        self.assertNotContains(home_response, "Важное тестовое уведомление")

    def test_anonymous_dismissal_is_saved_in_session_and_hides_notification(self):
        response = self.client.post(
            reverse("core:dismiss_system_notification", args=[self.visible_notification.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.session[ANONYMOUS_DISMISSED_NOTIFICATIONS_SESSION_KEY],
            [self.visible_notification.pk],
        )

        home_response = self.client.get(reverse("core:home"))
        self.assertNotContains(home_response, "Важное тестовое уведомление")

    def test_dismiss_endpoint_requires_post_and_rejects_inactive_notification(self):
        get_response = self.client.get(
            reverse("core:dismiss_system_notification", args=[self.visible_notification.pk])
        )
        inactive_response = self.client.post(
            reverse("core:dismiss_system_notification", args=[self.inactive_notification.pk])
        )

        self.assertEqual(get_response.status_code, 405)
        self.assertEqual(inactive_response.status_code, 400)

    def test_unsaved_notification_is_not_considered_currently_displayed(self):
        notification = SystemNotification(
            message_ru="Черновик уведомления",
            is_active=True,
        )

        self.assertFalse(notification.is_currently_displayed())
