from django.test import TestCase
from django.urls import reverse

from users.models import User
from users.tests import UserTest
from posts.models import Post


class PostTest(UserTest):
    def setUp(self):
        super().setUp()
        self.test_post = Post.objects.create(
            user=self.test_user_1,
            subject="Test",
            content="Test",
        )

    def tearDown(self):
        super().tearDown()
        Post.objects.all().delete()


class GetPostsByAdminTest(PostTest):
    def test_success_get_posts_by_admin(self):
        response = self.client.get(
            reverse("api-1.0.0:get_posts_by_admin"),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )

        results = {
            "items": [
                {
                    "id": self.test_post.id,
                    "created_at": f"{self.test_post.created_at.isoformat()[:-9]}Z",
                    "updated_at": f"{self.test_post.updated_at.isoformat()[:-9]}Z",
                    "subject": self.test_post.subject,
                    "image_url": self.test_post.image_url,
                    "user_id": self.test_user_1.id,
                    "user_nickname": self.test_user_1.nickname,
                    "user_thumbnail": self.test_user_1.thumbnail_url,
                    "post_likes_count": self.test_post.likes.count(),
                    "user_mbti": self.test_post.user.mbti,
                    "user_signup_time": f"{self.test_post.user.created_at.isoformat()[:-9]}Z",
                    "reported_count": self.test_post.reports.count(),
                }
            ],
            "count": Post.objects.filter(is_deleted=False).count(),
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    def test_fail_405_get_posts_by_admin(self):
        response = self.client.post(
            reverse("api-1.0.0:get_posts_by_admin"),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )

        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)
