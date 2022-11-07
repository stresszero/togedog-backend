from django.urls import reverse

from comments.models import Comment
from posts.models import Post
from users.tests import UserTest


class CommentTest(UserTest):
    def setUp(self):
        super().setUp()
        self.test_post = Post.objects.create(
            user=self.test_user_1,
            subject="Test",
            content="Test",
        )
        self.test_post_comment = Comment.objects.create(
            user=self.test_user_1,
            post=self.test_post,
            content="test comment",
        )

    def tearDown(self):
        super().tearDown()
        Post.objects.all().delete()
        Comment.objects.all().delete()


class CreateCommentTest(CommentTest):
    def test_success_create_comment(self):
        response = self.client.post(
            reverse("api-1.0.0:create_comment", kwargs={"post_id": self.test_post.id}),
            data={"content": "foo"},
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        comment = Comment.objects.get(id=response.json()["id"])
        results = {
            "id": comment.id,
            "created_at": f"{comment.created_at.isoformat()[:-9]}Z",
            "content": comment.content,
            "user_id": comment.user_id,
            "post_id": comment.post_id,
            "user_nickname": comment.user.nickname,
            "user_thumbnail": comment.user.thumbnail_url,
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    def test_fail_create_comment_with_invalid_post_id(self):
        response = self.client.post(
            reverse("api-1.0.0:create_comment", kwargs={"post_id": 12345}),
            data={"content": "foo"},
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_405_create_comment_with_invalid_method(self):
        response = self.client.get(
            reverse("api-1.0.0:create_comment", kwargs={"post_id": self.test_post.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_403_create_comment_with_invalid_token(self):
        self.test_user_1.status = "banned"
        self.test_user_1.save()
        response = self.client.post(
            reverse("api-1.0.0:create_comment", kwargs={"post_id": self.test_post.id}),
            data={"content": "foo"},
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_401_create_comment_with_invalid_token(self):
        response = self.client.post(
            reverse("api-1.0.0:create_comment", kwargs={"post_id": self.test_post.id}),
            data={"content": "foo"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})
