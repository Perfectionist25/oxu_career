from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from accounts.models import EmployerProfile, Company
from jobs.models import Job, JobApplication
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create test employer, companies and run dashboard checks'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'test_employer'
        password = 'TestPass123!'

        user, created = User.objects.get_or_create(username=username, defaults={
            'email': 'employer@example.com',
            'first_name': 'Test',
            'last_name': 'Employer',
            'user_type': 'employer',
        })
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created user {username} / {password}'))
        else:
            self.stdout.write(self.style.NOTICE(f'User {username} exists'))

        profile, _ = EmployerProfile.objects.get_or_create(user=user)

        # Remove any existing test companies we created in previous runs
        Company.objects.filter(owner=user, name__startswith='TEST COMPANY').delete()

        # Create 3 companies
        companies = []
        for i in range(1, 4):
            c = Company.objects.create(
                owner=user,
                name=f'TEST COMPANY {i}',
                description='Sample test company',
                email=f'contact{i}@example.com',
                phone=f'+123456789{i}',
                website=f'https://example{i}.com',
                is_active=True,
            )
            companies.append(c)

        # Create jobs for companies
        for idx, comp in enumerate(companies, start=1):
            for j in range(idx):
                job = Job.objects.create(
                    company=comp,
                    title=f'Test Job {comp.id}-{j+1}',
                    description='Test job description',
                    is_active=(j % 2 == 0),
                    created_at=timezone.now(),
                )
                # create one application for first job of company 1
                if idx == 1 and j == 0:
                    JobApplication.objects.create(job=job, user=user, cover_letter='Hi', created_at=timezone.now())

        # Now run test client checks
        client = Client()
        logged_in = client.login(username=username, password=password)
        if not logged_in:
            self.stdout.write(self.style.ERROR('Could not log in with test user.'))
            return
        self.stdout.write(self.style.SUCCESS('Logged in as test_employer'))

        base_url = '/accounts/employer/dashboard/'

        # 1) No company selected
        r = client.get(base_url)
        ok = r.status_code == 200 and b'Create your first company' not in r.content
        self.stdout.write(f'GET {base_url} -> {r.status_code} (no company param)')
        if b'Create your first company' in r.content:
            self.stdout.write(self.style.WARNING('Page shows create-first-company block (user has companies)'))

        # 2) select company 1
        cid = companies[0].id
        r1 = client.get(base_url, {'company_id': cid})
        self.stdout.write(f'GET {base_url}?company_id={cid} -> {r1.status_code}')
        found_company = companies[0].name.encode() in r1.content
        self.stdout.write(self.style.SUCCESS('Company name present in response' if found_company else 'Company name NOT found'))

        # 3) select company 2
        cid2 = companies[1].id
        r2 = client.get(base_url, {'company_id': cid2})
        self.stdout.write(f'GET {base_url}?company_id={cid2} -> {r2.status_code}')
        found_company2 = companies[1].name.encode() in r2.content
        self.stdout.write(self.style.SUCCESS('Company 2 present' if found_company2 else 'Company 2 NOT found'))

        # Check that selector links include ?company_id=
        has_selector = b'?company_id=' in r.content or b'?company_id=' in r1.content
        self.stdout.write(self.style.SUCCESS('Selector links include ?company_id=' if has_selector else 'Selector links DO NOT include company_id param'))

        # Quick actions links sanity
        qa_ok = b'jobs:job_create' in r.content or b'company_create' in r.content or b'My Jobs' in r.content
        self.stdout.write(self.style.SUCCESS('Quick Actions looks present' if qa_ok else 'Quick Actions may be missing'))

        self.stdout.write(self.style.SUCCESS('Test command finished'))
