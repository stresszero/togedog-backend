from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY
from django.urls import reverse

from comments.models import Comment, CommentDelete
from posts.models import Post, PostLike, PostDelete
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
        results = {
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
        self.assertEqual(response.json(), results)

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


class ModifyPostTest(PostTest):
    def test_success_without_file_modify_post(self):
        modify_data = {"subject": "modify_test", "content": "modify_test"}
        response = self.client.patch(
            reverse("api-1.0.0:modify_post", kwargs={"post_id": self.test_post.id}),
            data=encode_multipart(data=modify_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    @patch("cores.utils.file_handler")
    def test_success_with_file_modify_post(self, mock_patch):
        upload_file = ContentFile(b"foo", "bar.png")
        modify_data = {"subject": "qwer", "content": "qwer", "file": upload_file}

        mock_response = mock_patch.return_value
        mock_response.status_code = 200

        response = self.client.patch(
            reverse("api-1.0.0:modify_post", kwargs={"post_id": self.test_post.id}),
            data=encode_multipart(data=modify_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        mock_response.json.return_value = {"message": "success"}
        self.assertEqual(response.status_code, mock_response.status_code)
        self.assertEqual(response.json(), mock_response.json.return_value)

    def test_fail_400_modify_post(self):
        upload_file = ContentFile(b"foo", "foo.bar")
        modify_data = {"subject": "asdf", "content": "asdf", "file": upload_file}
        wrong_extension_response = self.client.patch(
            reverse("api-1.0.0:modify_post", kwargs={"post_id": self.test_post.id}),
            data=encode_multipart(data=modify_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(wrong_extension_response.status_code, 400)
        self.assertContains(
            wrong_extension_response, "invalid file extension", status_code=400
        )

        too_large_file = ContentFile(b"foo" * 1024 * 1024 * 51, "foo.png")
        modify_data["file"] = too_large_file
        too_large_file_response = self.client.patch(
            reverse("api-1.0.0:modify_post", kwargs={"post_id": self.test_post.id}),
            data=encode_multipart(data=modify_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(too_large_file_response.status_code, 400)
        self.assertContains(
            too_large_file_response, "file size is too large", status_code=400
        )

    def test_fail_401_modify_post(self):
        modify_data = {"subject": "modify_test", "content": "modify_test"}
        response = self.client.patch(
            reverse("api-1.0.0:modify_post", kwargs={"post_id": self.test_post.id}),
            data=encode_multipart(data=modify_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})

    def test_fail_403_modify_post(self):
        self.test_post.user_id = self.test_admin.id
        self.test_post.save()
        response = self.client.patch(
            reverse("api-1.0.0:modify_post", kwargs={"post_id": self.test_post.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_404_modify_post(self):
        response = self.client.patch(
            reverse("api-1.0.0:modify_post", kwargs={"post_id": 999}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})


class GetPostByAdminTest(PostTest):
    def test_success_get_post_by_admin(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:get_post_by_admin",
                kwargs={"post_id": self.test_post.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        results = {
            "id": self.test_post.id,
            "subject": self.test_post.subject,
            "content": self.test_post.content,
            "created_at": f"{self.test_post.created_at.isoformat()[:-9]}Z",
            "image_url": self.test_post.image_url,
            "user_id": self.test_post.user_id,
            "user_name": self.test_post.user.name,
            "user_nickname": self.test_post.user.nickname,
            "user_email": self.test_post.user.email,
            "user_mbti": self.test_post.user.mbti,
            "user_address": self.test_post.user.address,
            "user_thumbnail": self.test_post.user.thumbnail_url,
            "user_created_at": f"{self.test_post.user.created_at.isoformat()[:-9]}Z",
            "comments_list": [
                {
                    "id": comment.id,
                    "created_at": f"{comment.created_at.isoformat()[:-9]}Z",
                    "content": comment.content,
                    "user_id": comment.user_id,
                    "post_id": comment.post_id,
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

    def test_fail_405_get_post_by_admin(self):
        response = self.client.post(
            reverse(
                "api-1.0.0:get_post_by_admin",
                kwargs={"post_id": self.test_post.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_403_get_post_by_admin(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:get_post_by_admin",
                kwargs={"post_id": self.test_post.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})


class DeletePostTest(PostTest):
    def test_success_delete_post(self):
        response = self.client.post(
            reverse("api-1.0.0:delete_post", kwargs={"post_id": self.test_post.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        post = Post.objects.get(id=self.test_post.id)
        post_delete = PostDelete.objects.get(post_id=self.test_post.id)
        comments = Comment.objects.filter(post_id=self.test_post.id)
        comment_deletes = CommentDelete.objects.filter(
            comment_id=self.test_post_comment.id
        )

        self.assertEqual(post.is_deleted, True)
        self.assertEqual(post_delete.post_id, self.test_post.id)
        self.assertEqual(post_delete.delete_reason, "글쓴이 본인이 삭제")
        self.assertEqual(
            all(i.delete_reason == "게시글 삭제로 인한 댓글 자동삭제" for i in comment_deletes), True
        )
        self.assertEqual(comment_deletes.count(), comments.count())
        self.assertEqual(all(comment.is_deleted for comment in comments), True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_405_delete_post(self):
        response = self.client.get(
            reverse("api-1.0.0:delete_post", kwargs={"post_id": self.test_post.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)
    
    def test_fail_403_delete_post(self):
        self.test_post.user_id = self.test_admin.id
        self.test_post.save()
        response = self.client.post(
            reverse("api-1.0.0:delete_post", kwargs={"post_id": self.test_post.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_404_delete_post(self):
        response = self.client.post(
            reverse("api-1.0.0:delete_post", kwargs={"post_id": 12345}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})
        