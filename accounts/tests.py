from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from .middleware import BruteForceProtectionMiddleware
from .models import CustomUser, AdminProfile, EmployerProfile, StudentProfile


class AccountCreationTests(TestCase):
	def setUp(self):

		self.main_admin = CustomUser.objects.create_user(
		 username="mainadmin",
		 email="mainadmin@example.com",
		 password="adminpass",
		 user_type="main_admin",
		)

		Client().force_login(self.main_admin)
		self.client = Client()
		self.client.force_login(self.main_admin)
		self.admin = CustomUser.objects.create_user(
		 username="adminuser",
		 email="admin@example.com",
		 password="adminpass",
		 user_type="admin",
		)
		self.admin_profile, _ = AdminProfile.objects.get_or_create(user=self.admin)
		self.admin_profile.can_manage_employers = True
		self.admin_profile.save(update_fields=["can_manage_employers"])

	def test_create_admin_account_view_creates_single_profile(self):
		url = reverse("accounts:create_admin_account")
		data = {
		 "username": "newadmin",
		 "email": "newadmin@example.com",
		 "first_name": "New",
		 "last_name": "Admin",
		 "password1": "strongpass123",
		 "password2": "strongpass123",
		 "can_manage_students": True,
		 "can_manage_employers": True,
		 "can_manage_jobs": True,
		 "can_manage_resumes": True,
		 "can_view_statistics": True,
		}

		response = self.client.post(url, data)

		self.assertIn(response.status_code, (302, 301))

		user = CustomUser.objects.filter(username="newadmin").first()
		self.assertIsNotNone(user)

		profiles = AdminProfile.objects.filter(user=user)
		self.assertEqual(profiles.count(), 1)

	def test_create_admin_with_existing_username_shows_error(self):

		CustomUser.objects.create_user(
		 username="existingadmin",
		 email="exist@example.com",
		 password="pass123",
		 user_type="admin",
		)

		url = reverse("accounts:create_admin_account")
		data = {
		 "username": "existingadmin",
		 "email": "newemail@example.com",
		 "first_name": "New",
		 "last_name": "Admin",
		 "password1": "strongpass123",
		 "password2": "strongpass123",
		 "can_manage_students": True,
		 "can_manage_employers": True,
		 "can_manage_jobs": True,
		 "can_manage_resumes": True,
		 "can_view_statistics": True,
		}

		response = self.client.post(url, data)

		self.assertEqual(response.status_code, 200)

		self.assertTrue(
		 b"already exists" in response.content or
		 b"allaqachon" in response.content or
		 b"errorlist" in response.content
		)

		self.assertEqual(CustomUser.objects.filter(username="existingadmin").count(), 1)

	def test_create_employer_account_view_creates_single_profile(self):
		url = reverse("accounts:create_employer_account")
		data = {
		 "username": "newemployer",
		 "email": "emp@example.com",
		 "first_name": "New",
		 "last_name": "Employer",
		 "password1": "emppass123",
		 "password2": "emppass123",
		 "company_name": "ACME Ltd",
		 "company_description": "Test company",
		}

		response = self.client.post(url, data)
		self.assertIn(response.status_code, (302, 301))

		user = CustomUser.objects.filter(username="newemployer").first()
		self.assertIsNotNone(user)
		profiles = EmployerProfile.objects.filter(user=user)
		self.assertEqual(profiles.count(), 1)

	def test_admin_can_create_employer_account(self):
		self.client.force_login(self.admin)
		url = reverse("accounts:create_employer_account")
		data = {
		 "username": "managedemployer",
		 "email": "managed@example.com",
		 "first_name": "Managed",
		 "last_name": "Employer",
		 "password1": "emppass123",
		 "password2": "emppass123",
		 "company_name": "Managed ACME Ltd",
		 "company_description": "Managed test company",
		}

		response = self.client.post(url, data)
		self.assertIn(response.status_code, (302, 301))
		self.assertTrue(CustomUser.objects.filter(username="managedemployer", user_type="employer").exists())

	def test_temp_student_login_creates_profile_once(self):
		url = reverse("accounts:temp_student_login")
		response = self.client.post(url)

		self.assertIn(response.status_code, (302, 301))
		user = CustomUser.objects.filter(username="test_student").first()
		self.assertIsNotNone(user)
		profiles = StudentProfile.objects.filter(user=user)
		self.assertGreaterEqual(profiles.count(), 1)

		self.assertEqual(profiles.count(), 1)


class DjangoAdminBruteForceTests(TestCase):
	def setUp(self):
		cache.clear()
		self.client = Client()
		self.password = "StrongAdminPass123"
		self.admin_user = CustomUser.objects.create_user(
			username="django-admin-user",
			email="django-admin@example.com",
			password=self.password,
			user_type="admin",
			is_staff=True,
			is_superuser=True,
		)
		self.login_url = reverse("admin:login")
		self.ip_address = "127.0.0.1"

	def _login_payload(self, password):
		return {
			"username": self.admin_user.username,
			"password": password,
			"next": "/admin/",
		}

	def test_django_admin_login_is_blocked_after_too_many_failures(self):
		for _ in range(BruteForceProtectionMiddleware.MAX_ATTEMPTS):
			response = self.client.post(self.login_url, self._login_payload("wrong-password"))
			self.assertEqual(response.status_code, 200)

		blocked_response = self.client.post(
			self.login_url,
			self._login_payload("wrong-password"),
		)

		self.assertEqual(blocked_response.status_code, 429)
		self.assertContains(blocked_response, "too many failed login attempts", status_code=429)

	def test_successful_django_admin_login_clears_bruteforce_counters(self):
		for _ in range(3):
			self.client.post(self.login_url, self._login_payload("wrong-password"))

		ip_key = BruteForceProtectionMiddleware._attempts_ip_key(self.ip_address)
		user_key = BruteForceProtectionMiddleware._attempts_user_key(self.admin_user.username)
		self.assertEqual(cache.get(ip_key), 3)
		self.assertEqual(cache.get(user_key), 3)

		response = self.client.post(self.login_url, self._login_payload(self.password))

		self.assertEqual(response.status_code, 302)
		self.assertIsNone(cache.get(ip_key))
		self.assertIsNone(cache.get(user_key))
