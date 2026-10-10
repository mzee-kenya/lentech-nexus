from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationTests(APITestCase):
    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'lenox',
                'email': 'lenox@example.com',
                'password': 'Str0ng!pass',
                'password_confirm': 'Str0ng!pass',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='lenox').exists())
        self.assertIn('username', response.data)

        # The new user should be able to hit the "me" endpoint immediately.
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data['username'], 'lenox')

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'lenox',
                'email': 'lenox@example.com',
                'password': 'Str0ng!pass',
                'password_confirm': 'different',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(username='owner', email='same@example.com', password='x')
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'lenox',
                'email': 'SAME@example.com',
                'password': 'Str0ng!pass',
                'password_confirm': 'Str0ng!pass',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'lenox',
                'email': 'lenox@example.com',
                'password': '12345678',
                'password_confirm': '12345678',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginLogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='lenox', email='lenox@example.com', password='Str0ng!pass'
        )

    def test_login_with_username(self):
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'lenox', 'password': 'Str0ng!pass'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'lenox')
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.data['username'], 'lenox')

    def test_login_with_email(self):
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'lenox@example.com', 'password': 'Str0ng!pass'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_rejects_bad_credentials(self):
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'lenox', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_destroys_session(self):
        self.client.force_login(self.user)
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Token authentication is not used in this test; the session must be gone.
        self.client.force_authenticate(user=None)
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, status.HTTP_403_FORBIDDEN)


class AccountSettingsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='lenox', email='lenox@example.com', password='Str0ng!pass'
        )
        self.client.force_authenticate(user=self.user)

    def test_me_update_and_password_change(self):
        response = self.client.patch('/api/auth/me/', {'first_name': 'Lenox'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Lenox')

        response = self.client.post(
            '/api/auth/password/',
            {'old_password': 'Str0ng!pass', 'new_password': 'NewStr0ng!pass'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStr0ng!pass'))

    def test_me_cannot_promote_self(self):
        response = self.client.patch(
            '/api/auth/me/', {'is_staff': True, 'role': 'admin'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)

    def test_password_change_requires_correct_old_password(self):
        response = self.client.post(
            '/api/auth/password/',
            {'old_password': 'wrong', 'new_password': 'NewStr0ng!pass'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserDirectoryTests(APITestCase):
    def setUp(self):
        self.me = User.objects.create_user(
            username='me', email='me@example.com', password='Str0ng!pass'
        )
        self.bob = User.objects.create_user(
            username='bob', email='bob@example.com', password='Str0ng!pass', first_name='Bob'
        )
        self.carol = User.objects.create_user(
            username='carol', email='carol@example.com', password='Str0ng!pass'
        )

    def test_requires_authentication(self):
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lists_others_and_excludes_self(self):
        self.client.force_authenticate(user=self.me)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = {u['username'] for u in response.data['results']}
        self.assertEqual(usernames, {'bob', 'carol'})

    def test_search_filters_results(self):
        self.client.force_authenticate(user=self.me)
        response = self.client.get('/api/auth/users/?search=bob')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['username'], 'bob')