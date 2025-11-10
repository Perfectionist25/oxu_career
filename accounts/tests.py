from django.test import TestCase, Client
from django.urls import reverse

from .models import CustomUser, AdminProfile, EmployerProfile, StudentProfile


class AccountCreationTests(TestCase):
	def setUp(self):
		# Create a main admin who can create other admins/employers
		self.main_admin = CustomUser.objects.create_user(
			username="mainadmin",
			email="mainadmin@example.com",
			password="adminpass",
			user_type="main_admin",
		)
		# Ensure main_admin has a profile created by signal (if signals active)
		Client().force_login(self.main_admin)
		self.client = Client()
		self.client.force_login(self.main_admin)

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
		# Should redirect on success
		self.assertIn(response.status_code, (302, 301))

		user = CustomUser.objects.filter(username="newadmin").first()
		self.assertIsNotNone(user)
		# Ensure exactly one AdminProfile exists for this user
		profiles = AdminProfile.objects.filter(user=user)
		self.assertEqual(profiles.count(), 1)

	def test_create_admin_with_existing_username_shows_error(self):
		# Create an existing user
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
		# Form should be re-rendered with error (status 200)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b"allaqachon", response.content)
		# No duplicate user created
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

	def test_temp_student_login_creates_profile_once(self):
		url = reverse("accounts:temp_student_login")
		response = self.client.post(url)
		# After login it redirects
		self.assertIn(response.status_code, (302, 301))
		user = CustomUser.objects.filter(username="test_student").first()
		self.assertIsNotNone(user)
		profiles = StudentProfile.objects.filter(user=user)
		self.assertGreaterEqual(profiles.count(), 1)
		# Should not create duplicates
		self.assertEqual(profiles.count(), 1)
