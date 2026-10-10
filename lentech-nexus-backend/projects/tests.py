from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Project, ProjectJoinRequest, ProjectMembership

User = get_user_model()


class ProjectApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='Str0ng!pass'
        )
        self.member = User.objects.create_user(
            username='member', email='member@example.com', password='Str0ng!pass'
        )
        self.client.force_authenticate(user=self.owner)

    def _project(self, owner=None, **kwargs):
        owner = owner or self.owner
        return Project.objects.create(
            owner=owner, title=kwargs.pop('title', 'Nexus App'), **kwargs
        )

    def test_list_is_public_with_member_count(self):
        project = self._project()
        ProjectMembership.objects.create(project=project, user=self.owner, role='owner')
        ProjectMembership.objects.create(project=project, user=self.member)
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['member_count'], 2)
        self.assertEqual(response.data['results'][0]['owner_username'], 'owner')

    def test_anonymous_cannot_create(self):
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/projects/', {'title': 'X'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_sets_owner_and_membership(self):
        response = self.client.post(
            '/api/projects/',
            {'title': 'Nexus API', 'summary': 'Backend', 'technologies': ['Django']},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get()
        self.assertEqual(project.owner_id, self.owner.id)
        self.assertTrue(
            ProjectMembership.objects.filter(project=project, user=self.owner).exists()
        )
        self.assertEqual(
            ProjectMembership.objects.get(project=project, user=self.owner).role, 'owner'
        )

    def test_non_owner_cannot_update_or_delete(self):
        project = self._project(owner=self.member)
        response = self.client.patch(f'/api/projects/{project.id}/', {'title': 'Hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(f'/api/projects/{project.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_update_and_delete(self):
        project = self._project(owner=self.owner)
        response = self.client.patch(f'/api/projects/{project.id}/', {'status': 'in_progress'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(f'/api/projects/{project.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_filter_by_status_and_search(self):
        self._project(owner=self.owner, status='planning')
        self._project(owner=self.owner, title='Shiny Rocket', status='completed')
        response = self.client.get('/api/projects/', {'status': 'completed'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Shiny Rocket')
        response = self.client.get('/api/projects/', {'search': 'rocket'})
        self.assertEqual(response.data['count'], 1)


class ProjectCollaborationTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='Str0ng!pass'
        )
        self.member = User.objects.create_user(
            username='member', email='member@example.com', password='Str0ng!pass'
        )
        self.project = Project.objects.create(owner=self.owner, title='Nexus App')

    def test_anonymous_cannot_join(self):
        response = self.client.post(f'/api/projects/{self.project.id}/join/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_join_creates_pending_request(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f'/api/projects/{self.project.id}/join/', {'message': 'I can help'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ProjectJoinRequest.objects.filter(project=self.project, requester=self.member).exists()
        )

    def test_owner_cannot_join_own_project(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f'/api/projects/{self.project.id}/join/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_pending_request_rejected(self):
        ProjectJoinRequest.objects.create(project=self.project, requester=self.member)
        self.client.force_authenticate(user=self.member)
        response = self.client.post(f'/api/projects/{self.project.id}/join/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_requests_only_visible_and_reviewable_by_owner(self):
        request_obj = ProjectJoinRequest.objects.create(project=self.project, requester=self.member)
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/projects/{self.project.id}/requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.post(f'/api/join-requests/{request_obj.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            ProjectMembership.objects.filter(project=self.project, user=self.member).exists()
        )

        # A second review attempt must fail.
        response = self.client.post(f'/api/join-requests/{request_obj.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_join_requests_outside_scope_hidden(self):
        request_obj = ProjectJoinRequest.objects.create(project=self.project, requester=self.member)
        stranger = User.objects.create_user(
            username='stranger', email='stranger@example.com', password='Str0ng!pass'
        )
        self.client.force_authenticate(user=stranger)
        # The stranger can list only their own requests: none.
        response = self.client.get('/api/join-requests/')
        self.assertEqual(response.data['count'], 0)
        # The request itself is not retrievable by a stranger.
        response = self.client.get(f'/api/join-requests/{request_obj.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_requester_can_cancel_pending_request(self):
        request_obj = ProjectJoinRequest.objects.create(project=self.project, requester=self.member)
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(f'/api/join-requests/{request_obj.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'cancelled')

    def test_leave_removes_membership(self):
        ProjectMembership.objects.create(project=self.project, user=self.member)
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(f'/api/projects/{self.project.id}/leave/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ProjectMembership.objects.filter(project=self.project, user=self.member).exists()
        )

    def test_owner_cannot_leave(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(f'/api/projects/{self.project.id}/leave/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_remove_member(self):
        ProjectMembership.objects.create(project=self.project, user=self.member)
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(
            f'/api/projects/{self.project.id}/members/{self.member.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)