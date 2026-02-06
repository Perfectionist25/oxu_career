from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from urllib.parse import urlparse, parse_qs


class Command(BaseCommand):
    help = 'Test employer dashboard as logged-in test_employer user'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'test_employer'
        password = 'TestPass123!'

        client = Client()
        logged_in = client.login(username=username, password=password)
        if not logged_in:
            self.stdout.write(self.style.ERROR('Could not log in as test_employer'))
            return

        self.stdout.write(self.style.SUCCESS('✓ Logged in as test_employer'))

        base_url = '/accounts/employer/dashboard/'
        response = client.get(base_url)

        # Test 1: Status code
        test1_pass = response.status_code == 200
        self.stdout.write(self.style.SUCCESS(f'✓ GET {base_url} -> {response.status_code}') if test1_pass else self.style.ERROR(f'✗ GET {base_url} -> {response.status_code} (expected 200)'))

        # Test 2: Page title
        test2_pass = b'Employer Dashboard' in response.content
        self.stdout.write(self.style.SUCCESS('✓ "Employer Dashboard" title found') if test2_pass else self.style.WARNING('✗ "Employer Dashboard" title not found'))

        # Test 3: Greeting with username
        test3_pass = b'Welcome' in response.content and b'test' in response.content.lower()
        self.stdout.write(self.style.SUCCESS('✓ Welcome greeting with username found') if test3_pass else self.style.WARNING('✗ Welcome greeting not found'))

        # Test 4: Quick Actions present
        test4_pass = (b'Add Company' in response.content or b'New Job' in response.content) and b'Quick Actions' in response.content
        self.stdout.write(self.style.SUCCESS('✓ Quick Actions section found with buttons') if test4_pass else self.style.WARNING('✗ Quick Actions section missing or incomplete'))

        # Test 5: My Companies section
        test5_pass = b'My Companies' in response.content and b'TEST COMPANY' in response.content
        self.stdout.write(self.style.SUCCESS('✓ "My Companies" section found with company list') if test5_pass else self.style.WARNING('✗ "My Companies" section missing or no companies shown'))

        # Test 6: Company selector with ?company_id= links
        test6_pass = b'?company_id=' in response.content
        self.stdout.write(self.style.SUCCESS('✓ Company selector links with ?company_id= found') if test6_pass else self.style.WARNING('✗ Company selector links missing'))

        # Test 7: Statistics cards
        test7_pass = b'Active Jobs' in response.content and b'Total Applications' in response.content
        self.stdout.write(self.style.SUCCESS('✓ Statistics cards (Active Jobs, Applications) visible') if test7_pass else self.style.WARNING('✗ Statistics cards not found'))

        # Test 8: Recent Jobs section
        test8_pass = b'Recent Jobs' in response.content
        self.stdout.write(self.style.SUCCESS('✓ "Recent Jobs" section found') if test8_pass else self.style.WARNING('✗ "Recent Jobs" section missing'))

        # Test 9: No NoReverseMatch errors in content (sanity check)
        test9_pass = b'NoReverseMatch' not in response.content and b'Reverse for' not in response.content
        self.stdout.write(self.style.SUCCESS('✓ No template URL errors in response') if test9_pass else self.style.ERROR('✗ Template URL errors detected in response'))

        # Test 10: Check response has no 500 error pages
        test10_pass = response.status_code != 500 and b'Internal Server Error' not in response.content
        self.stdout.write(self.style.SUCCESS('✓ No 500 errors') if test10_pass else self.style.ERROR('✗ Server error detected'))

        # Summary
        all_pass = all([test1_pass, test2_pass, test3_pass, test4_pass, test5_pass, test6_pass, test7_pass, test8_pass, test9_pass, test10_pass])
        self.stdout.write('')
        if all_pass:
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('✓ ALL TESTS PASSED - Dashboard is working correctly!'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
        else:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('⚠ Some tests did not pass, please review above'))
            self.stdout.write(self.style.WARNING('=' * 60))
