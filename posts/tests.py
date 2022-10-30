from django.urls import reverse

from comments.models import Comment
from posts.models import Post, PostLike
from users.tests import UserTest


class PostTest(UserTest):
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
        self.test_post_like = PostLike.objects.create(
            like_user=self.test_user_1,
            post=self.test_post,
        )
        self.test_deleted_post = Post.objects.create(
            user=self.test_user_1,
            subject="Test2",
            content="Test2",
            is_deleted=True,
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

    def test_fail_403_get_posts_by_admin(self):
        response = self.client.get(
            reverse("api-1.0.0:get_posts_by_admin"),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})


class GetDeletedPostsTest(PostTest):
    def test_success_get_deleted_posts(self):
        response = self.client.get(
            reverse("api-1.0.0:get_deleted_posts"),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        results = {
            "items": [
                {
                    "id": self.test_deleted_post.id,
                    "created_at": f"{self.test_deleted_post.created_at.isoformat()[:-9]}Z",
                    "updated_at": f"{self.test_deleted_post.updated_at.isoformat()[:-9]}Z",
                    "user": self.test_deleted_post.user.id,
                    "subject": self.test_deleted_post.subject,
                    "content": self.test_deleted_post.content,
                    "image_url": self.test_deleted_post.image_url,
                    "is_deleted": self.test_deleted_post.is_deleted,
                    "user_nickname": self.test_deleted_post.user.nickname,
                    "user_mbti": self.test_deleted_post.user.mbti,
                }
            ],
            "count": Post.objects.filter(is_deleted=True).count(),
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    def test_fail_405_get_deleted_posts(self):
        response = self.client.post(
            reverse("api-1.0.0:get_deleted_posts"),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )

        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_403_get_deleted_posts(self):
        response = self.client.get(
            reverse("api-1.0.0:get_deleted_posts"),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})


class GetDeletedPostByAdmin(PostTest):
    def test_success_get_deleted_post_by_admin(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:get_deleted_post_by_admin",
                kwargs={"post_id": self.test_deleted_post.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        result = {
            "id": self.test_deleted_post.id,
            "subject": self.test_deleted_post.subject,
            "content": self.test_deleted_post.content,
            "created_at": f"{self.test_deleted_post.created_at.isoformat()[:-9]}Z",
            "image_url": self.test_deleted_post.image_url,
            "user_id": self.test_deleted_post.user.id,
            "user_name": self.test_deleted_post.user.nickname,
            "user_nickname": self.test_deleted_post.user.nickname,
            "user_email": self.test_deleted_post.user.email,
            "user_mbti": self.test_deleted_post.user.mbti,
            "user_address": self.test_deleted_post.user.address,
            "user_thumbnail": self.test_deleted_post.user.thumbnail_url,
            "user_created_at": f"{self.test_deleted_post.user.created_at.isoformat()[:-9]}Z",
            "delete_reason": "등록된 삭제사유 없음",
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), result)

    def test_fail_405_get_deleted_post_by_admin(self):
        response = self.client.post(
            reverse(
                "api-1.0.0:get_deleted_post_by_admin",
                kwargs={"post_id": self.test_deleted_post.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_403_get_deleted_post_by_admin(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:get_deleted_post_by_admin",
                kwargs={"post_id": self.test_deleted_post.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})


class GetPostTest(PostTest):
    def test_success_get_post(self):
        response = self.client.get(
            reverse("api-1.0.0:get_post", kwargs={"post_id": self.test_post.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )

        results = {
            "id": self.test_post.id,
            "user_id": self.test_post.user_id,
            "user_nickname": self.test_post.user.nickname,
            "user_thumbnail": self.test_post.user.thumbnail_url,
            "subject": self.test_post.subject,
            "content": self.test_post.content,
            "image_url": self.test_post.image_url,
            "created_at": f"{self.test_post.created_at.isoformat()[:-9]}Z",
            "post_likes_count": self.test_post.get_likes_count,
            "is_liked": self.test_post.likes.filter(
                like_user_id=self.test_user_1.id
            ).exists(),
            "comments_list": [
                {
                    "content": comment.content,
                    "created_at": f"{comment.created_at.isoformat()[:-9]}Z",
                    "id": comment.id,
                    "post_id": comment.post_id,
                    "user_id": comment.user_id,
                    "user_nickname": comment.user.nickname,
                    "user_thumbnail": comment.user.thumbnail_url,
                }
                for comment in self.test_post.comments.filter(
                    is_deleted=False
                ).order_by("created_at")
            ],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    def test_fail_405_get_post(self):
        response = self.client.post(
            reverse("api-1.0.0:get_post", kwargs={"post_id": self.test_post.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )

        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_403_get_post(self):
        self.test_user_1.status = "banned"
        self.test_user_1.save()
        response = self.client.get(
            reverse("api-1.0.0:get_post", kwargs={"post_id": self.test_post.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_401_get_post(self):
        response = self.client.get(
            reverse("api-1.0.0:get_post", kwargs={"post_id": self.test_post.id})
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})
