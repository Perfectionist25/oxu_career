from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import EmployerProfile, Company
from jobs.models import Job


class Command(BaseCommand):
    help = "Create test employer, company and job to verify ownership flow"

    def handle(self, *args, **options):
        User = get_user_model()
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username="employer_test",
                defaults={"email": "employer_test@example.com"},
            )
            if created:
                user.set_password("testpass123")
                user.is_active = True
                user.user_type = "employer"
                user.is_active_employer = True
                user.save()

            profile, pcreated = EmployerProfile.objects.get_or_create(user=user)

            try:
                company, ccreated = Company.objects.get_or_create(
                    owner=profile,
                    name="Test Company",
                    defaults={
                        "company_type": "LLC",
                        "description": "Automated test company",
                        "short_description": "Test company",
                        "phone": "+998901234567",
                        "region": "Tashkent",
                        "city": "Tashkent",
                        "address": "Test address",
                        "industry": "IT",
                        "is_active": True,
                        "is_verified": True,
                    },
                )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed creating company: {e}"))
                return

            try:
                job, jcreated = Job.objects.get_or_create(
                    company=company,
                    title="Test Job",
                    defaults={
                        "description": "Automated test job description",
                        "short_description": "Test job",
                        "work_type": "office",
                        "employment_type": "full_time",
                        "experience_level": "no_experience",
                        "education_level": "none",
                        "requirements": "None",
                        "responsibilities": "Testing",
                        "skills_required": "testing",
                        "contact_email": "hr@example.com",
                        "is_active": True,
                    },
                )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed creating job: {e}"))
                return

            self.stdout.write(self.style.SUCCESS(f"user id={user.id} created={created}"))
            self.stdout.write(self.style.SUCCESS(f"profile id={profile.id} created={pcreated}"))
            self.stdout.write(self.style.SUCCESS(f"company id={company.id} created={ccreated}"))
            self.stdout.write(self.style.SUCCESS(f"job id={job.id} created={jcreated}"))
