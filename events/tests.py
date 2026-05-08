from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Company, CustomUser

from .models import Event, EventCategory, EventEmployerCategory, EventParticipation


class EventParticipationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = EventCategory.objects.create(name="Career")
        self.event = Event.objects.create(
            title="Career Meetup",
            short_description="Meet people",
            description="Meet people and companies",
            category=self.category,
            event_type="networking",
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=2, hours=2),
            location="Main Hall",
            max_participants=2,
            status="published",
        )
        self.student = CustomUser.objects.create_user(
            username="student1",
            password="testpass123",
            user_type="student",
            email="student1@example.com",
        )
        self.student_two = CustomUser.objects.create_user(
            username="student2",
            password="testpass123",
            user_type="student",
            email="student2@example.com",
        )
        self.employer = CustomUser.objects.create_user(
            username="employer1",
            password="testpass123",
            user_type="employer",
            email="employer1@example.com",
            is_active_employer=True,
        )
        Company.objects.create(
            name="Bank Corp",
            company_type="LLC",
            owner=self.employer,
            industry="Bank",
            is_active=True,
        )
        self.admin = CustomUser.objects.create_user(
            username="admin1",
            password="testpass123",
            user_type="admin",
            email="admin1@example.com",
            is_staff=True,
        )

    def test_student_can_register_for_event(self):
        self.client.login(username="student1", password="testpass123")

        response = self.client.post(reverse("events:join_event", args=[self.event.slug]))

        self.assertRedirects(response, reverse("events:event_detail", args=[self.event.slug]))
        self.assertTrue(
            EventParticipation.objects.filter(
                event=self.event,
                user=self.student,
                status=EventParticipation.STATUS_REGISTERED,
            ).exists()
        )

    def test_alumni_can_register_for_event(self):
        alumni = CustomUser.objects.create_user(
            username="alumni1",
            password="testpass123",
            user_type="alumni",
            email="alumni1@example.com",
        )
        self.client.login(username="alumni1", password="testpass123")

        response = self.client.post(reverse("events:join_event", args=[self.event.slug]))

        self.assertRedirects(response, reverse("events:event_detail", args=[self.event.slug]))
        self.assertTrue(
            EventParticipation.objects.filter(
                event=self.event,
                user=alumni,
                status=EventParticipation.STATUS_REGISTERED,
            ).exists()
        )

    def test_capacity_is_enforced(self):
        EventParticipation.objects.create(event=self.event, user=self.student, role="student")
        EventParticipation.objects.create(event=self.event, user=self.student_two, role="student")
        third_student = CustomUser.objects.create_user(
            username="student3",
            password="testpass123",
            user_type="student",
        )

        self.client.login(username="student3", password="testpass123")
        response = self.client.post(reverse("events:join_event", args=[self.event.slug]), follow=True)

        self.assertContains(response, "No seats left for this event.")
        self.assertFalse(
            EventParticipation.objects.filter(event=self.event, user=third_student).exists()
        )

    def test_employer_category_restriction_is_enforced(self):
        allowed_category = EventEmployerCategory.objects.create(name="Bank")
        self.event.allowed_employer_categories.add(allowed_category)
        other_employer = CustomUser.objects.create_user(
            username="employer2",
            password="testpass123",
            user_type="employer",
            email="employer2@example.com",
            is_active_employer=True,
        )
        Company.objects.create(
            name="Tech Corp",
            company_type="LLC",
            owner=other_employer,
            industry="Technology",
            is_active=True,
        )

        self.client.login(username="employer2", password="testpass123")
        response = self.client.post(reverse("events:join_event", args=[self.event.slug]), follow=True)

        self.assertContains(response, "Only eligible employers can register for this event.")
        self.assertFalse(
            EventParticipation.objects.filter(event=self.event, user=other_employer).exists()
        )

    def test_cannot_cancel_after_event_started(self):
        participation = EventParticipation.objects.create(
            event=self.event, user=self.student, role="student"
        )
        self.event.start_date = timezone.now() - timedelta(minutes=5)
        self.event.end_date = timezone.now() + timedelta(hours=1)
        self.event.save()

        self.client.login(username="student1", password="testpass123")
        response = self.client.post(
            reverse("events:cancel_registration", args=[self.event.slug]), follow=True
        )

        participation.refresh_from_db()
        self.assertContains(response, "Participation can no longer be cancelled.")
        self.assertEqual(participation.status, EventParticipation.STATUS_REGISTERED)

    def test_check_in_is_one_time(self):
        participation = EventParticipation.objects.create(
            event=self.event, user=self.student, role="student"
        )

        participation.mark_attended(checked_in_by=self.admin)
        self.assertEqual(participation.attendance_status, EventParticipation.ATTENDANCE_ATTENDED)

        with self.assertRaisesMessage(ValidationError, "QR code already used."):
            participation.mark_attended(checked_in_by=self.admin)

    def test_check_in_is_blocked_after_event_end(self):
        participation = EventParticipation.objects.create(
            event=self.event, user=self.student, role="student"
        )
        self.event.start_date = timezone.now() - timedelta(hours=2)
        self.event.end_date = timezone.now() - timedelta(minutes=1)
        self.event.save()

        with self.assertRaisesMessage(
            ValidationError, "Check-in is closed because the event has ended."
        ):
            participation.mark_attended(checked_in_by=self.admin)
