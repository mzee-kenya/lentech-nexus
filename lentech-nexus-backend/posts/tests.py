from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Comment, Post, PostLike

User = get_user_model()


@override_settings(CLOUDINARY_ENABLED=False)
class PostApiTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='author', email='author@example.com', password='Str0ng!pass'
        )
        self.other = User.objects.create_user(
            username='other', email='other@example.com', password='Str0ng!pass'
        )
        self.client.force_authenticate(user=self.author)

    def _post(self, author=None, **kwargs):
        return Post.objects.create(author=author or self.author, **kwargs)

    def test_list_is_public(self):
        self._post(body='hello')
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_anonymous_cannot_create(self):
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/posts/', {'body': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_text_post_sets_author_and_counts(self):
        response = self.client.post('/api/posts/', {'body': 'Hello world'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.get().author_id, self.author.id)
        self.assertEqual(response.data['like_count'], 0)
        self.assertEqual(response.data['viewer_has_liked'], False)

    def test_create_requires_body_or_media(self):
        response = self.client.post('/api/posts/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_media_rejected_when_storage_disabled(self):
        upload = SimpleUploadedFile('pic.jpg', b'binary', content_type='image/jpeg')
        response = self.client.post('/api/posts/', {'image': upload}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)

    def test_non_author_cannot_update_or_delete(self):
        post = self._post(author=self.other, body='original')
        response = self.client.patch(f'/api/posts/{post.id}/', {'body': 'hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(f'/api/posts/{post.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_update_and_delete(self):
        post = self._post(author=self.author, body='original')
        response = self.client.patch(f'/api/posts/{post.id}/', {'body': 'edited'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(f'/api/posts/{post.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=post.id).exists())


class PostLikeTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='author', email='author@example.com', password='Str0ng!pass'
        )
        self.other = User.objects.create_user(
            username='other', email='other@example.com', password='Str0ng!pass'
        )
        self.post = Post.objects.create(author=self.author, body='like me')
        self.client.force_authenticate(user=self.other)

    def test_like_is_idempotent(self):
        response = self.client.post(f'/api/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['like_count'], 1)
        self.assertEqual(response.data['viewer_has_liked'], True)
        # Liking twice must not create a second row.
        self.client.post(f'/api/posts/{self.post.id}/like/')
        self.assertEqual(PostLike.objects.filter(post=self.post).count(), 1)

    def test_unlike_is_idempotent(self):
        PostLike.objects.create(post=self.post, user=self.other)
        response = self.client.delete(f'/api/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['like_count'], 0)
        # Unliking again should not error.
        response = self.client.delete(f'/api/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_like(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(f'/api/posts/{self.post.id}/like/')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class CommentTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='author', email='author@example.com', password='Str0ng!pass'
        )
        self.other = User.objects.create_user(
            username='other', email='other@example.com', password='Str0ng!pass'
        )
        self.post = Post.objects.create(author=self.author, body='discuss')

    def test_comment_thread_is_public_and_post_requires_auth(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.post(
            f'/api/posts/{self.post.id}/comments/', {'body': 'Nice!'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comment.objects.filter(post=self.post, author=self.other).exists())

        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/posts/{self.post.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_empty_comment_rejected(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.post(
            f'/api/posts/{self.post.id}/comments/', {'body': '   '}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_comment_author_can_delete(self):
        comment = Comment.objects.create(post=self.post, author=self.other, body='mine')
        self.client.force_authenticate(user=self.author)
        response = self.client.delete(f'/api/comments/{comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f'/api/comments/{comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
