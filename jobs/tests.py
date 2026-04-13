from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Company
from .models import Job, SavedJob, ViewedJob


User = get_user_model()


class StudentJobTrackingTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student_test",
            password="testpass123",
            email="student@example.com",
            user_type="student",
        )
        self.employer = User.objects.create_user(
            username="employer_test",
            password="testpass123",
            email="employer@example.com",
            user_type="employer",
        )
        self.company = Company.objects.create(
            owner=self.employer,
            name="OXU Labs",
            company_type="LLC",
            industry="IT",
            is_active=True,
        )
        self.job = Job.objects.create(
            title="Junior Python Developer",
            short_description="Entry-level backend role for students.",
            description="Build internal services and assist the engineering team.",
            company=self.company,
            created_by=self.employer.employer_profile,
            job_market="uzbekistan",
            location="Tashkent",
            work_type="office",
            employment_type="internship",
            experience_level="intern",
            education_level="bachelor",
            requirements="Python basics and willingness to learn.",
            responsibilities="Support the product team and write simple features.",
            skills_required="Python, Django",
            contact_email="hr@oxu.test",
            expires_at=timezone.now() + timedelta(days=10),
            is_active=True,
        )
        self.client.force_login(self.student)

    def test_job_detail_persists_viewed_job_for_student(self):
        url = reverse("jobs:job_detail", args=[self.job.pk])

        first_response = self.client.get(url)
        self.assertEqual(first_response.status_code, 200)
        self.assertTrue(ViewedJob.objects.filter(user=self.student, job=self.job).exists())

        self.job.refresh_from_db()
        self.assertEqual(self.job.views_count, 1)

        second_response = self.client.get(url)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(ViewedJob.objects.filter(user=self.student, job=self.job).count(), 1)

        self.job.refresh_from_db()
        self.assertEqual(self.job.views_count, 1)

    def test_job_list_marks_saved_and_viewed_jobs_in_context(self):
        SavedJob.objects.create(user=self.student, job=self.job)
        ViewedJob.objects.create(user=self.student, job=self.job)

        response = self.client.get(reverse("jobs:list"))
        self.assertEqual(response.status_code, 200)

        jobs_by_id = {job.id: job for job in response.context["jobs"].object_list}
        tracked_job = jobs_by_id[self.job.id]

        self.assertTrue(tracked_job.is_saved)
        self.assertTrue(tracked_job.is_viewed)
        self.assertEqual(response.context["saved_jobs_count"], 1)
        self.assertEqual(response.context["viewed_jobs_count"], 1)

    def test_save_and_unsave_job_ajax_updates_saved_count_and_favorites(self):
        save_response = self.client.post(
            reverse("jobs:save_job", args=[self.job.pk]),
            {"next": reverse("jobs:list")},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(save_response.status_code, 200)
        self.assertTrue(SavedJob.objects.filter(user=self.student, job=self.job).exists())
        self.assertEqual(save_response.json()["saved_jobs_count"], 1)

        self.job.refresh_from_db()
        self.assertEqual(self.job.favorites_count, 1)

        unsave_response = self.client.post(
            reverse("jobs:unsave_job", args=[self.job.pk]),
            {"next": reverse("jobs:list")},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(unsave_response.status_code, 200)
        self.assertFalse(SavedJob.objects.filter(user=self.student, job=self.job).exists())
        self.assertEqual(unsave_response.json()["saved_jobs_count"], 0)

        self.job.refresh_from_db()
        self.assertEqual(self.job.favorites_count, 0)

    def test_unsave_job_redirects_back_to_saved_jobs_when_no_next(self):
        SavedJob.objects.create(user=self.student, job=self.job)
        response = self.client.post(reverse("jobs:unsave_job", args=[self.job.pk]))

        self.assertRedirects(response, reverse("jobs:saved_jobs"))
