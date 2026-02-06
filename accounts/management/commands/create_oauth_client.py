from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create an OAuth2 application for student API (password grant)."

    def handle(self, *args, **options):
        try:
            from oauth2_provider.models import Application
            from django.contrib.auth import get_user_model
        except Exception as exc:
            self.stderr.write("Required package oauth2_provider not available. Install requirements and run migrations.")
            return

        User = get_user_model()
        # find a superuser to own the application
        owner = User.objects.filter(is_superuser=True).first()
        if not owner:
            self.stderr.write("No superuser found. Create a superuser first.")
            return

        app, created = Application.objects.get_or_create(
            name="student-password-client",
            defaults={
                "user": owner,
                "client_type": Application.CLIENT_CONFIDENTIAL,
                "authorization_grant_type": Application.GRANT_PASSWORD,
            },
        )

        if created:
            self.stdout.write("Created OAuth2 application:")
        else:
            self.stdout.write("OAuth2 application already exists (updated credentials shown):")

        self.stdout.write(f"Client ID: {app.client_id}")
        self.stdout.write(f"Client Secret: {app.client_secret}")