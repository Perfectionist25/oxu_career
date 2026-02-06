# accounts/tests/test_oauth.py - OAuth 2.0 Authentication Tests
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import logging

from accounts.models import StudentProfile, OAuthToken
from accounts.oauth_backend import UniversityOAuthBackend

User = get_user_model()
logger = logging.getLogger(__name__)


class OAuthBackendTests(TestCase):
    """Test cases for OAuth 2.0 backend authentication"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.backend = UniversityOAuthBackend()
        self.factory = RequestFactory()
        self.mock_user_data = {
            "id": "test_student_123",
            "email": "test@university.edu",
            "first_name": "Test",
            "last_name": "Student",
            "student_id": "20240001",
        }
        self.mock_token_response = {
            "access_token": "test_access_token_12345",
            "refresh_token": "test_refresh_token_12345",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "openid profile email student_info",
        }
    
    @patch('accounts.oauth_backend.requests.post')
    def test_get_access_token_success(self, mock_post):
        """Test successful token exchange"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_token_response
        mock_post.return_value = mock_response
        
        result = self.backend.get_access_token(code="test_auth_code")
        
        self.assertEqual(result['access_token'], 'test_access_token_12345')
        self.assertEqual(result['token_type'], 'Bearer')
        self.assertEqual(result['expires_in'], 3600)
    
    @patch('accounts.oauth_backend.requests.post')
    def test_get_access_token_failure(self, mock_post):
        """Test token exchange failure"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid_code"}
        mock_post.return_value = mock_response
        
        result = self.backend.get_access_token(code="invalid_code")
        
        self.assertIsNone(result)
    
    @patch('accounts.oauth_backend.requests.get')
    def test_get_user_info_success(self, mock_get):
        """Test successful user info retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_user_data
        mock_get.return_value = mock_response
        
        result = self.backend.get_user_info(access_token="test_token")
        
        self.assertEqual(result['email'], 'test@university.edu')
        self.assertEqual(result['student_id'], '20240001')
    
    @patch('accounts.oauth_backend.requests.get')
    def test_get_user_info_failure(self, mock_get):
        """Test user info retrieval failure"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "invalid_token"}
        mock_get.return_value = mock_response
        
        result = self.backend.get_user_info(access_token="invalid_token")
        
        self.assertIsNone(result)
    
    def test_get_or_create_user_new_user(self):
        """Test creating a new user from OAuth data"""
        user_data = self.mock_user_data.copy()
        
        user = self.backend.get_or_create_user(user_data)
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@university.edu')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.user_type, 'student')
        
        # Check if StudentProfile was created
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())
    
    def test_get_or_create_user_existing_user(self):
        """Test updating an existing user"""
        # Create existing user
        user = User.objects.create_user(
            username='test_student',
            email='test@university.edu',
            user_type='student'
        )
        StudentProfile.objects.create(user=user)
        
        user_data = self.mock_user_data.copy()
        user_data['first_name'] = 'Updated'
        
        result_user = self.backend.get_or_create_user(user_data)
        
        self.assertEqual(result_user.id, user.id)
        self.assertEqual(result_user.first_name, 'Updated')
    
    def test_save_oauth_token(self):
        """Test saving OAuth token to database"""
        user = User.objects.create_user(
            username='test_student',
            email='test@university.edu',
            user_type='student'
        )
        
        token_data = self.mock_token_response.copy()
        
        oauth_token = self.backend.save_oauth_token(user, token_data)
        
        self.assertIsNotNone(oauth_token)
        self.assertEqual(oauth_token.user, user)
        self.assertEqual(oauth_token.access_token, 'test_access_token_12345')
        self.assertEqual(oauth_token.token_type, 'Bearer')
        self.assertTrue(oauth_token.expires_at)
    
    @patch('accounts.oauth_backend.requests.post')
    @patch('accounts.oauth_backend.requests.get')
    def test_authenticate_full_flow(self, mock_get, mock_post):
        """Test complete OAuth authentication flow"""
        # Mock token response
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = self.mock_token_response
        mock_post.return_value = mock_token_response
        
        # Mock user info response
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = self.mock_user_data
        mock_get.return_value = mock_user_response
        
        request = self.factory.get('/')
        request.session = {}
        
        user = self.backend.authenticate(
            request=request,
            code='test_auth_code',
            state='test_state'
        )
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@university.edu')
        
        # Verify OAuth token was saved
        oauth_token = OAuthToken.objects.get(user=user)
        self.assertEqual(oauth_token.access_token, 'test_access_token_12345')


class OAuthTokenModelTests(TestCase):
    """Test cases for OAuthToken model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='test_student',
            email='test@university.edu',
            user_type='student'
        )
    
    def test_oauth_token_creation(self):
        """Test creating an OAuthToken"""
        token = OAuthToken.objects.create(
            user=self.user,
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_type='Bearer',
            expires_in=3600,
            scope='openid profile email',
        )
        
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.access_token, 'test_access_token')
        self.assertIsNotNone(token.expires_at)
    
    def test_oauth_token_is_expired(self):
        """Test token expiration check"""
        # Create expired token
        expired_token = OAuthToken.objects.create(
            user=self.user,
            access_token='expired_token',
            refresh_token='refresh_token',
            token_type='Bearer',
            expires_in=3600,
        )
        # Manually set expires_at to past
        expired_token.expires_at = timezone.now() - timedelta(hours=1)
        expired_token.save()
        
        self.assertTrue(expired_token.is_expired())
        
        # Create valid token
        valid_token = OAuthToken.objects.create(
            user=self.user,
            access_token='valid_token',
            refresh_token='refresh_token2',
            token_type='Bearer',
            expires_in=3600,
        )
        
        self.assertFalse(valid_token.is_expired())
    
    @patch('accounts.oauth_backend.UniversityOAuthBackend.get_access_token')
    def test_oauth_token_refresh(self, mock_get_token):
        """Test token refresh"""
        token = OAuthToken.objects.create(
            user=self.user,
            access_token='old_token',
            refresh_token='refresh_token',
            token_type='Bearer',
            expires_in=3600,
        )
        
        # Mock new token response
        mock_get_token.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
        }
        
        result = token.refresh_access_token()
        
        self.assertTrue(result)
        token.refresh_from_db()
        self.assertEqual(token.access_token, 'new_access_token')


class OAuthViewsTests(TestCase):
    """Test cases for OAuth views"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.factory = RequestFactory()
    
    def test_student_oauth_login_redirects(self):
        """Test OAuth login view redirects to provider"""
        response = self.client.get(reverse('accounts:oauth_login'))
        
        # Should redirect to OAuth provider
        self.assertEqual(response.status_code, 302)
        self.assertIn('oauth.university.edu', response.url)
    
    def test_student_oauth_login_creates_session_state(self):
        """Test OAuth login creates state in session"""
        response = self.client.get(reverse('accounts:oauth_login'))
        
        # Check session was modified
        self.assertIn('oauth_state', self.client.session)
    
    @patch('accounts.oauth_backend.UniversityOAuthBackend.authenticate')
    def test_oauth_callback_success(self, mock_authenticate):
        """Test OAuth callback with valid code"""
        user = User.objects.create_user(
            username='test_student',
            email='test@university.edu',
            user_type='student'
        )
        StudentProfile.objects.create(user=user)
        
        mock_authenticate.return_value = user
        
        # Set up session with state
        session = self.client.session
        session['oauth_state'] = 'test_state'
        session.save()
        
        response = self.client.get(
            reverse('accounts:oauth_callback'),
            {'code': 'test_code', 'state': 'test_state'},
            follow=False
        )
        
        # Should redirect after successful authentication
        self.assertIn(response.status_code, [301, 302])
    
    def test_oauth_callback_state_mismatch(self):
        """Test OAuth callback rejects mismatched state"""
        # Set up session with one state
        session = self.client.session
        session['oauth_state'] = 'valid_state'
        session.save()
        
        # Request with different state
        response = self.client.get(
            reverse('accounts:oauth_callback'),
            {'code': 'test_code', 'state': 'invalid_state'}
        )
        
        # Should reject and redirect
        self.assertEqual(response.status_code, 302)
        self.assertIn('hemis_login', response.url)
