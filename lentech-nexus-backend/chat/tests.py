from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Conversation, ConversationMember, Message

User = get_user_model()


class ConversationTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username='alice', email='alice@example.com', password='Str0ng!pass'
        )
        self.bob = User.objects.create_user(
            username='bob', email='bob@example.com', password='Str0ng!pass'
        )
        self.carol = User.objects.create_user(
            username='carol', email='carol@example.com', password='Str0ng!pass'
        )
        self.client.force_authenticate(user=self.alice)

    def test_direct_chat_creation_adds_both_members(self):
        response = self.client.post(
            '/api/conversations/', {'kind': 'direct', 'member_ids': [self.bob.id]}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        conversation = Conversation.objects.get()
        self.assertEqual(conversation.kind, 'direct')
        self.assertEqual(conversation.members.count(), 2)
        self.assertEqual(response.data['member_count'], 2)

    def test_direct_chat_is_deduplicated(self):
        first = self.client.post(
            '/api/conversations/', {'kind': 'direct', 'member_ids': [self.bob.id]}, format='json'
        )
        second = self.client.post(
            '/api/conversations/', {'kind': 'direct', 'member_ids': [self.bob.id]}, format='json'
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data['id'], second.data['id'])
        self.assertEqual(Conversation.objects.count(), 1)

    def test_conversation_list_is_scoped_to_member(self):
        # A conversation between bob and carol must be invisible to alice.
        other = Conversation.objects.create(kind='direct', created_by=self.bob)
        ConversationMember.objects.create(conversation=other, user=self.bob)
        ConversationMember.objects.create(conversation=other, user=self.carol)

        response = self.client.get('/api/conversations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get(f'/api/conversations/{other.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_group_requires_title_and_member(self):
        response = self.client.post(
            '/api/conversations/', {'kind': 'group', 'member_ids': [self.bob.id]}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            '/api/conversations/', {'kind': 'group', 'title': 'Team'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            '/api/conversations/',
            {'kind': 'group', 'title': 'Study Group', 'member_ids': [self.bob.id, self.carol.id]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['member_count'], 3)
        self.assertEqual(response.data['viewer_role'], 'owner')

    def test_direct_chat_requires_exactly_one_member(self):
        response = self.client.post(
            '/api/conversations/', {'kind': 'direct', 'member_ids': []}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MessageTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username='alice', email='alice@example.com', password='Str0ng!pass'
        )
        self.bob = User.objects.create_user(
            username='bob', email='bob@example.com', password='Str0ng!pass'
        )
        self.conversation = Conversation.objects.create(kind='direct', created_by=self.alice)
        ConversationMember.objects.create(conversation=self.conversation, user=self.alice)
        ConversationMember.objects.create(conversation=self.conversation, user=self.bob)

    def test_member_can_send_and_read_messages(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            f'/api/conversations/{self.conversation.id}/messages/',
            {'body': 'Hi Bob'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Message.objects.filter(conversation=self.conversation, sender=self.alice).exists()
        )

        self.client.force_authenticate(user=self.bob)
        response = self.client.get(f'/api/conversations/{self.conversation.id}/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_empty_message_rejected(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            f'/api/conversations/{self.conversation.id}/messages/', {'body': '  '}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_member_cannot_read_messages(self):
        stranger = User.objects.create_user(
            username='stranger', email='stranger@example.com', password='Str0ng!pass'
        )
        self.client.force_authenticate(user=stranger)
        response = self.client.get(f'/api/conversations/{self.conversation.id}/messages/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_sending_message_bumps_conversation(self):
        before = Conversation.objects.get(pk=self.conversation.pk).updated_at
        self.client.force_authenticate(user=self.bob)
        self.client.post(
            f'/api/conversations/{self.conversation.id}/messages/', {'body': 'hi'}, format='json'
        )
        after = Conversation.objects.get(pk=self.conversation.pk).updated_at
        self.assertGreaterEqual(after, before)


class GroupMembershipTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='Str0ng!pass'
        )
        self.member = User.objects.create_user(
            username='member', email='member@example.com', password='Str0ng!pass'
        )
        self.outsider = User.objects.create_user(
            username='outsider', email='outsider@example.com', password='Str0ng!pass'
        )
        self.group = Conversation.objects.create(
            kind='group', title='Team', created_by=self.owner
        )
        ConversationMember.objects.create(
            conversation=self.group, user=self.owner, role=ConversationMember.Role.OWNER
        )
        ConversationMember.objects.create(conversation=self.group, user=self.member)

    def test_add_member_to_group(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f'/api/conversations/{self.group.id}/members/',
            {'user_id': self.outsider.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.group.members.filter(user=self.outsider).exists())

    def test_owner_can_remove_member(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(
            f'/api/conversations/{self.group.id}/members/{self.member.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.group.members.filter(user=self.member).exists())

    def test_plain_member_cannot_remove_others(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(
            f'/api/conversations/{self.group.id}/members/{self.owner.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_add_member_to_direct_chat(self):
        direct = Conversation.objects.create(kind='direct', created_by=self.owner)
        ConversationMember.objects.create(conversation=direct, user=self.owner)
        ConversationMember.objects.create(conversation=direct, user=self.member)
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f'/api/conversations/{direct.id}/members/',
            {'user_id': self.outsider.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_member_can_leave(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(f'/api/conversations/{self.group.id}/leave/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.group.members.filter(user=self.member).exists())


class UnreadNotificationTests(APITestCase):
    """Unread counting that powers the navbar message badge."""

    def setUp(self):
        self.alice = User.objects.create_user(
            username='alice', email='alice@example.com', password='Str0ng!pass'
        )
        self.bob = User.objects.create_user(
            username='bob', email='bob@example.com', password='Str0ng!pass'
        )
        self.conversation = Conversation.objects.create(kind='direct', created_by=self.alice)
        ConversationMember.objects.create(conversation=self.conversation, user=self.alice)
        ConversationMember.objects.create(conversation=self.conversation, user=self.bob)

    def test_incoming_messages_count_and_reading_clears_them(self):
        # Bob sends two messages; Alice has not opened the thread yet.
        self.client.force_authenticate(user=self.bob)
        for body in ('Hi', 'Are you there?'):
            self.client.post(
                f'/api/conversations/{self.conversation.id}/messages/',
                {'body': body},
                format='json',
            )

        # The unread endpoint reports both messages for Alice.
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/conversations/unread/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread'], 2)

        # The conversation list also exposes a per-thread count.
        listing = self.client.get('/api/conversations/')
        self.assertEqual(listing.data['results'][0]['unread_count'], 2)

        # Opening the thread marks it read and drops the count to zero.
        self.client.get(f'/api/conversations/{self.conversation.id}/messages/')
        response = self.client.get('/api/conversations/unread/')
        self.assertEqual(response.data['unread'], 0)

    def test_own_messages_are_never_unread(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post(
            f'/api/conversations/{self.conversation.id}/messages/',
            {'body': 'Talking to myself'},
            format='json',
        )
        response = self.client.get('/api/conversations/unread/')
        self.assertEqual(response.data['unread'], 0)

    def test_unread_endpoint_requires_authentication(self):
        response = self.client.get('/api/conversations/unread/')
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )


class ConversationAccessTests(APITestCase):
    """Access control and small model behaviours."""

    def test_anonymous_cannot_list_conversations(self):
        response = self.client.get('/api/conversations/')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_message_model_str(self):
        user = User.objects.create_user(
            username='u', email='u@example.com', password='Str0ng!pass'
        )
        conversation = Conversation.objects.create(kind='direct', created_by=user)
        message = Message.objects.create(conversation=conversation, sender=user, body='hello')
        self.assertEqual(str(message), f'{user.id}: hello')
