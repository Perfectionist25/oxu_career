from datetime import timedelta
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.forms import StudentCertificateForm
from accounts.models import (
    Company,
    CustomUser,
    EmployerProfile,
    StudentCertificate,
    StudentProfile,
)
from jobs.models import Job, JobApplication


class StudentCertificateAccessTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_media_root = tempfile.mkdtemp(prefix="student-cert-media-")
        cls.temp_protected_root = tempfile.mkdtemp(prefix="student-cert-protected-")
        cls.settings_override = override_settings(
            MEDIA_ROOT=cls.temp_media_root,
            PROTECTED_MEDIA_ROOT=cls.temp_protected_root,
        )
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        shutil.rmtree(cls.temp_media_root, ignore_errors=True)
        shutil.rmtree(cls.temp_protected_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.student_user = CustomUser.objects.create_user(
            username="certificate-student",
            email="student-cert@example.com",
            password="studentpass123",
            user_type="student",
        )
        self.student_profile = StudentProfile.objects.create(user=self.student_user)

        self.employer_user = CustomUser.objects.create_user(
            username="certificate-employer",
            email="employer-cert@example.com",
            password="employerpass123",
            user_type="employer",
            is_active_employer=True,
        )
        self.employer_profile = EmployerProfile.objects.create(user=self.employer_user)
        self.company = Company.objects.create(
            name="Certificate Company",
            company_type="llc",
            owner=self.employer_user,
            is_active=True,
        )
        self.job = Job.objects.create(
            title="Backend Developer",
            description="Job description",
            short_description="Short description",
            company=self.company,
            created_by=self.employer_profile,
            location="Tashkent",
            work_type="office",
            employment_type="full_time",
            experience_level="junior",
            education_level="bachelor",
            requirements="Python, Django",
            responsibilities="Build APIs",
            skills_required="Python, Django",
            contact_email="hr@example.com",
            expires_at=timezone.now() + timedelta(days=30),
        )
        JobApplication.objects.create(
            job=self.job,
            user=self.student_user,
            cover_letter="I am interested.",
        )

        self.other_employer = CustomUser.objects.create_user(
            username="outside-employer",
            email="outside@example.com",
            password="outsidepass123",
            user_type="employer",
            is_active_employer=True,
        )
        EmployerProfile.objects.create(user=self.other_employer)

        self.certificate = StudentCertificate.objects.create(
            student=self.student_profile,
            title="Python Certificate",
            file=SimpleUploadedFile(
                "python-certificate.pdf",
                b"%PDF-1.4\n%Test certificate\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
                content_type="application/pdf",
            ),
            issuer="OXU Career",
            is_active=True,
        )

    def test_student_certificate_form_rejects_unsupported_extension(self):
        form = StudentCertificateForm(
            data={
                "title": "Bad file",
                "is_active": True,
            },
            files={
                "file": SimpleUploadedFile(
                    "bad-file.txt",
                    b"plain text",
                    content_type="text/plain",
                )
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_related_employer_can_access_certificate_file(self):
        self.client.force_login(self.employer_user)

        response = self.client.get(
            reverse("accounts:student_certificate_file", args=[self.certificate.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_unrelated_employer_cannot_access_certificate_file(self):
        self.client.force_login(self.other_employer)

        response = self.client.get(
            reverse("accounts:student_certificate_file", args=[self.certificate.pk])
        )

        self.assertEqual(response.status_code, 403)
