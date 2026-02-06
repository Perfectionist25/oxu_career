from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import CustomUser
from cvbuilder.models import CV, CVTemplate


class PublicCVAccessTests(TestCase):
	def setUp(self):
		# create a published CV
		self.user = CustomUser.objects.create_user(
			username="alice",
			email="alice@example.com",
			password="pass123",
			user_type="student",
		)
		self.template = CVTemplate.objects.create(
			name="Default",
			thumbnail="",
			template_file="default.html",
			is_active=True,
		)
		self.cv = CV.objects.create(
			user=self.user,
			title="Dev CV",
			template=self.template,
			status="published",
			full_name="Alice",
			email="alice@example.com",
			phone="123",
			location="City",
			summary="About",
		)

		# clients
		self.client = Client()
		self.employer = CustomUser.objects.create_user(
			username="employer",
			email="emp@example.com",
			password="emppass",
			user_type="employer",
		)
		self.admin = CustomUser.objects.create_user(
			username="admin",
			email="admin@example.com",
			password="adminpass",
			user_type="admin",
		)

	def test_employer_can_access_public_list(self):
		self.client.login(username="employer", password="emppass")
		url = reverse("cvbuilder:public_cv_list")
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "Alice")

	def test_admin_can_access_public_list(self):
		self.client.login(username="admin", password="adminpass")
		url = reverse("cvbuilder:public_cv_list")
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "Alice")

	def test_student_cannot_access_public_list(self):
		self.client.login(username="alice", password="pass123")
		url = reverse("cvbuilder:public_cv_list")
		resp = self.client.get(url)
		# Redirect to cv_list with error
		self.assertIn(resp.status_code, (302, 301))
