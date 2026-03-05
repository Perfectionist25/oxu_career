from django.core.management.base import BaseCommand
from accounts.models import EmployerProfile, Company

class Command(BaseCommand):
    help = 'Fix primary company references to inactive companies'

    def handle(self, *args, **kwargs):

        profiles = EmployerProfile.objects.filter(
            primary_company__isnull=False,
            primary_company__is_active=False
        )

        fixed_count = 0
        for profile in profiles:

            active_company = Company.objects.filter(
                owner=profile.user,
                is_active=True
            ).first()

            if active_company:
                profile.primary_company = active_company
                self.stdout.write(f'Fixed {profile.user.username}: {profile.primary_company.name} → {active_company.name}')
            else:
                profile.primary_company = None
                self.stdout.write(f'Cleared {profile.user.username}: no active companies')

            profile.save()
            fixed_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Fixed {fixed_count} employer profiles')
        )