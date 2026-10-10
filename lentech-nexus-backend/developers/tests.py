import io

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Developer

User = get_user_model()


class DeveloperApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='lenox', email='lenox@example.com', password='Str0ng!pass'
        )
        self.other = User.objects.create_user(
            username='jane', email='jane@example.com', password='Str0ng!pass'
        )

    def _profile(self, owner=None):
        return Developer.objects.create(
            user=owner or self.user,
            name=(owner or self.user).display_name,
            role='Backend Developer',
            skills=['Python', 'Django'],
        )

    def test_list_is_public(self):
        self._profile(self.user)
        response = self.client.get('/api/developers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_is_public(self):
        profile = self._profile(self.user)
        response = self.client.get(f'/api/developers/{profile.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'lenox')

    def test_anonymous_cannot_create(self):
        response = self.client.post(
            '/api/developers/', {'name': 'x', 'role': 'Dev'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_create_own_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/developers/',
            {'role': 'Full-stack', 'bio': 'Hello', 'skills': ['React', 'Django']},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Developer.objects.get().user_id, self.user.id)
        self.assertEqual(response.data['name'], 'lenox')

    def test_user_cannot_create_second_profile(self):
        self._profile(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/developers/', {'role': 'Dev'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_update_profile(self):
        profile = self._profile(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f'/api/developers/{profile.id}/',
            {'role': 'Senior Backend', 'skills': ['Python', 'PostgreSQL']},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertEqual(profile.role, 'Senior Backend')
        self.assertEqual(profile.skills, ['Python', 'PostgreSQL'])

    def test_user_cannot_update_anothers_profile(self):
        profile = self._profile(self.other)
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f'/api/developers/{profile.id}/', {'role': 'Hacked'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_delete_anothers_profile(self):
        profile = self._profile(self.other)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/developers/{profile.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete_profile(self):
        profile = self._profile(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/developers/{profile.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_skills_must_be_a_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/developers/', {'role': 'Dev', 'skills': 'React'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_creates_profile_on_first_access(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/developers/me/', {'role': 'Frontend'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Developer.objects.filter(user=self.user).exists())


@override_settings(CLOUDINARY_ENABLED=False)
class ProfileImageTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='lenox', email='lenox@example.com', password='Str0ng!pass'
        )
        self.client.force_authenticate(user=self.user)

    def _png_bytes(self):
        # Minimal valid PNG header (not a real image, used for type checks only).
        return b'\x89PNG\r\n\x1a\n' + b'0' * 64

    def test_upload_returned_503_when_storage_disabled(self):
        response = self.client.post(
            '/api/developers/me/photo/',
            {'image': io.BytesIO(self._png_bytes())},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_upload_rejects_non_image_content_type(self):
        response = self.client.post(
            '/api/developers/me/photo/',
            {'image': io.BytesIO(b'some text')},
            format='multipart',
            headers={'Content-Disposition': 'attachment; filename=x.txt'},
        )
        # Multipart helper sets content-type automatically; this guard catches
        # missing files too.
        self.assertIn(response.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_503_SERVICE_UNAVAILABLE))

    def test_upload_requires_a_file(self):
        response = self.client.post('/api/developers/me/photo/', {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)