from django.test import TestCase
from django.contrib.auth import authenticate
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import datetime

from .models import User, Message, Follow, Favorite, Notification
from recipe.models import Recipe  # Assuming recipe app exists


class UserModelTestCase(TestCase):
    """Test cases for User model."""

    def setUp(self):
        """Set up test users."""
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

    def test_user_creation(self):
        """Test user creation."""
        self.assertEqual(self.user1.username, 'testuser1')
        self.assertEqual(self.user1.email, 'test1@example.com')
        self.assertTrue(self.user1.check_password('testpass123'))

    def test_user_string_representation(self):
        """Test user string representation."""
        expected = f"{self.user1.username} ({self.user1.email})"
        self.assertEqual(str(self.user1), expected)

    def test_follow_user(self):
        """Test following a user."""
        result = self.user1.follow(self.user2)
        self.assertTrue(result)
        self.assertTrue(self.user1.is_following(self.user2))
        self.assertIn(self.user2, self.user1.follows.all())

    def test_cannot_follow_self(self):
        """Test that user cannot follow themselves."""
        result = self.user1.follow(self.user1)
        self.assertFalse(result)

    def test_unfollow_user(self):
        """Test unfollowing a user."""
        self.user1.follow(self.user2)
        self.user1.unfollow(self.user2)
        self.assertFalse(self.user1.is_following(self.user2))

    def test_follower_count(self):
        """Test follower count."""
        self.user1.follow(self.user2)
        self.assertEqual(self.user2.get_follower_count(), 1)

    def test_following_count(self):
        """Test following count."""
        self.user1.follow(self.user2)
        self.assertEqual(self.user1.get_following_count(), 1)


class MessageModelTestCase(TestCase):
    """Test cases for Message model."""

    def setUp(self):
        """Set up test data."""
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            email='receiver@example.com',
            password='testpass123'
        )

    def test_message_creation(self):
        """Test message creation."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Hello, this is a test message'
        )
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)
        self.assertEqual(message.content, 'Hello, this is a test message')
        self.assertFalse(message.is_read)

    def test_mark_message_as_read(self):
        """Test marking message as read."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message'
        )
        message.mark_as_read()
        self.assertTrue(message.is_read)
        self.assertIsNotNone(message.read_at)


class UserRegistrationAPITestCase(APITestCase):
    """Test cases for user registration endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.register_url = '/api/v1/users/register/'

    def test_user_registration_success(self):
        """Test successful user registration."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_duplicate_username(self):
        """Test registration with duplicate username."""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123'
        )
        data = {
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        """Test registration with duplicate email."""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123'
        )
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password_confirm': 'different123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_short_password(self):
        """Test registration with short password."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'short',
            'password_confirm': 'short'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginAPITestCase(APITestCase):
    """Test cases for user login endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.login_url = '/api/v1/users/login/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        """Test successful login."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user."""
        data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileAPITestCase(APITestCase):
    """Test cases for user profile endpoints."""

    def setUp(self):
        """Set up test client and users."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

    def test_get_user_profile(self):
        """Test retrieving user profile."""
        url = f'/api/v1/users/{self.user.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_update_own_profile(self):
        """Test updating own profile."""
        self.client.force_authenticate(user=self.user)
        url = f'/api/v1/users/{self.user.id}/'
        data = {
            'bio': 'Updated bio',
            'social_links': {'twitter': 'https://twitter.com/testuser'}
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Updated bio')

    def test_cannot_update_others_profile(self):
        """Test that user cannot update others' profile."""
        self.client.force_authenticate(user=self.user)
        url = f'/api/v1/users/{self.other_user.id}/'
        data = {'bio': 'Hacked bio'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FollowAPITestCase(APITestCase):
    """Test cases for follow endpoints."""

    def setUp(self):
        """Set up test client and users."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.target_user = User.objects.create_user(
            username='target',
            email='target@example.com',
            password='testpass123'
        )

    def test_follow_user(self):
        """Test following a user via API."""
        self.client.force_authenticate(user=self.user)
        url = f'/api/v1/users/{self.target_user.id}/follow/'
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.is_following(self.target_user))

    def test_cannot_follow_self(self):
        """Test that user cannot follow themselves."""
        self.client.force_authenticate(user=self.user)
        url = f'/api/v1/users/{self.user.id}/follow/'
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unfollow_user(self):
        """Test unfollowing a user."""
        self.user.follow(self.target_user)
        self.client.force_authenticate(user=self.user)
        url = f'/api/v1/users/{self.target_user.id}/follow/'
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.user.is_following(self.target_user))


class MessagingAPITestCase(APITestCase):
    """Test cases for messaging endpoints."""

    def setUp(self):
        """Set up test client and users."""
        self.client = APIClient()
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            email='receiver@example.com',
            password='testpass123'
        )

    def test_send_message(self):
        """Test sending a message."""
        self.client.force_authenticate(user=self.sender)
        url = f'/api/v1/users/{self.sender.id}/messages/'
        data = {
            'receiver': self.receiver.id,
            'content': 'Hello, receiver!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Message.objects.filter(
            sender=self.sender,
            receiver=self.receiver,
            content='Hello, receiver!'
        ).exists())

    def test_list_messages(self):
        """Test listing messages."""
        Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message'
        )
        self.client.force_authenticate(user=self.receiver)
        url = f'/api/v1/users/{self.receiver.id}/messages/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_mark_message_as_read(self):
        """Test marking message as read."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message'
        )
        self.client.force_authenticate(user=self.receiver)
        url = f'/api/v1/users/{self.receiver.id}/messages/{message.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message.refresh_from_db()
        self.assertTrue(message.is_read)


class GDPRTestCase(APITestCase):
    """Test cases for GDPR endpoints."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_gdpr_data_export(self):
        """Test GDPR data export."""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/users/gdpr/export/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_gdpr_account_deletion(self):
        """Test GDPR account deletion."""
        self.client.force_authenticate(user=self.user)
        user_id = self.user.id
        url = '/api/v1/users/gdpr/delete/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=user_id).exists())
