from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Idea, IdeaInterest

User = get_user_model()


class IdeaApiTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='author', email='author@example.com', password='Str0ng!pass'
        )
        self.other = User.objects.create_user(
            username='other', email='other@example.com', password='Str0ng!pass'
        )
        self.client.force_authenticate(user=self.author)

    def _idea(self, author=None, **kwargs):
        author = author or self.author
        return Idea.objects.create(
            author=author,
            title=kwargs.pop('title', 'Learn French App'),
            **kwargs,
        )

    def test_list_is_public(self):
        self._idea(author=self.author)
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/ideas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_anonymous_cannot_create(self):
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/ideas/', {'title': 'X'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_sets_author(self):
        response = self.client.post(
            '/api/ideas/', {'title': 'Study Buddy', 'tags': ['education']}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Idea.objects.get().author_id, self.author.id)

    def test_non_author_cannot_update_or_delete(self):
        idea = self._idea(author=self.other)
        response = self.client.patch(f'/api/ideas/{idea.id}/', {'title': 'Hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(f'/api/ideas/{idea.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_update_status_and_delete(self):
        idea = self._idea(author=self.author)
        response = self.client.patch(f'/api/ideas/{idea.id}/', {'status': 'in_progress'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(f'/api/ideas/{idea.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class IdeaInterestTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='author', email='author@example.com', password='Str0ng!pass'
        )
        self.other = User.objects.create_user(
            username='other', email='other@example.com', password='Str0ng!pass'
        )
        self.stranger = User.objects.create_user(
            username='stranger', email='stranger@example.com', password='Str0ng!pass'
        )
        self.idea = Idea.objects.create(author=self.author, title='Study Buddy')

    def test_interest_flow_creates_pending(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.post(
            f'/api/ideas/{self.idea.id}/interest/', {'message': 'I love this'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(IdeaInterest.objects.filter(idea=self.idea, user=self.other).exists())

    def test_author_cannot_interest_own_idea(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.post(f'/api/ideas/{self.idea.id}/interest/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_pending_interest_rejected(self):
        IdeaInterest.objects.create(idea=self.idea, user=self.other)
        self.client.force_authenticate(user=self.other)
        response = self.client.post(f'/api/ideas/{self.idea.id}/interest/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_archived_idea_rejects_interest(self):
        self.idea.status = 'archived'
        self.idea.save()
        self.client.force_authenticate(user=self.other)
        response = self.client.post(f'/api/ideas/{self.idea.id}/interest/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_author_accepts_interest(self):
        interest = IdeaInterest.objects.create(idea=self.idea, user=self.other)
        self.client.force_authenticate(user=self.author)
        response = self.client.post(f'/api/idea-interests/{interest.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        interest.refresh_from_db()
        self.assertEqual(interest.status, 'accepted')

    def test_only_author_can_review_interest(self):
        interest = IdeaInterest.objects.create(idea=self.idea, user=self.other)
        self.client.force_authenticate(user=self.stranger)
        response = self.client.post(f'/api/idea-interests/{interest.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_withdraw_own_interest(self):
        interest = IdeaInterest.objects.create(idea=self.idea, user=self.other)
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f'/api/idea-interests/{interest.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        interest.refresh_from_db()
        self.assertEqual(interest.status, 'withdrawn')

    def test_interests_only_visible_to_author(self):
        IdeaInterest.objects.create(idea=self.idea, user=self.other)
        self.client.force_authenticate(user=self.stranger)
        response = self.client.get(f'/api/ideas/{self.idea.id}/interests/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.author)
        response = self.client.get(f'/api/ideas/{self.idea.id}/interests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)