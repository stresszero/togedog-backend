import json

from django.urls import reverse

from comments.models import Comment, CommentReport
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

    def test_fail_405_create_comment_with_invalid_method(self):
        response = self.client.get(
            reverse("api-1.0.0:create_comment", kwargs={"post_id": self.test_post.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_404_create_comment_with_invalid_post_id(self):
        response = self.client.post(
            reverse("api-1.0.0:create_comment", kwargs={"post_id": 12345}),
            data={"content": "foo"},
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

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


class DeleteCommentTest(CommentTest):
    def test_success_delete_comment(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        comment = Comment.objects.get(id=self.test_post_comment.id)
        self.assertTrue(comment.is_deleted)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_405_delete_comment(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:delete_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_404_delete_comment_with_invalid_post_id(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_comment",
                kwargs={"post_id": 12345, "comment_id": self.test_post_comment.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_404_delete_comment_with_invalid_comment_id(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_comment",
                kwargs={"post_id": self.test_post.id, "comment_id": 12345},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_403_delete_comment(self):
        self.test_user_1.status = "banned"
        self.test_user_1.save()
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_401_delete_comment(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})


class ModifyCommentTest(CommentTest):
    def test_success_modify_comment(self):
        response = self.client.patch(
            reverse(
                "api-1.0.0:modify_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            data=json.dumps({"content": "foo"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        comment = Comment.objects.get(id=self.test_post_comment.id)
        self.assertEqual(comment.content, "foo")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_405_modify_comment(self):
        response = self.client.put(
            reverse(
                "api-1.0.0:modify_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_404_modify_comment_with_invalid_post_id(self):
        response = self.client.patch(
            reverse(
                "api-1.0.0:modify_comment",
                kwargs={"post_id": 12345, "comment_id": self.test_post_comment.id},
            ),
            data=json.dumps({"content": "foo"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_404_modify_comment_with_invalid_comment_id(self):
        response = self.client.patch(
            reverse(
                "api-1.0.0:modify_comment",
                kwargs={"post_id": self.test_post.id, "comment_id": 12345},
            ),
            data=json.dumps({"content": "foo"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_403_modify_comment_by_banned_user(self):
        self.test_user_1.status = "banned"
        self.test_user_1.save()
        response = self.client.patch(
            reverse(
                "api-1.0.0:modify_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            data=json.dumps({"content": "foo"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_403_modify_comment_by_invalid_user(self):
        self.test_post_comment.user_id = self.test_admin.id
        self.test_post_comment.save()
        response = self.client.patch(
            reverse(
                "api-1.0.0:modify_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            data=json.dumps({"content": "foo"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_401_modify_comment(self):
        response = self.client.patch(
            reverse(
                "api-1.0.0:modify_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            data=json.dumps({"content": "foo"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})


class ReportCommentTest(CommentTest):
    def test_success_report_comment(self):
        response = self.client.post(
            reverse(
                "api-1.0.0:report_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            data={"content": "test report"},
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        comment_report = CommentReport.objects.get(
            reporter_user_id=self.test_admin.id,
            comment_id=self.test_post_comment.id,
        )
        self.assertEqual(comment_report.reporter_user_id, self.test_admin.id)
        self.assertEqual(comment_report.reported_user_id, self.test_user_1.id)
        self.assertEqual(comment_report.comment_id, self.test_post_comment.id)
        self.assertEqual(comment_report.content, "test report")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_405_report_comment(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:report_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_404_report_comment_with_invalid_post_id(self):
        response = self.client.post(
            reverse(
                "api-1.0.0:report_comment",
                kwargs={"post_id": 12345, "comment_id": self.test_post_comment.id},
            ),
            data={"content": "test report"},
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_404_report_comment_with_invalid_comment_id(self):
        response = self.client.post(
            reverse(
                "api-1.0.0:report_comment",
                kwargs={"post_id": self.test_post.id, "comment_id": 12345},
            ),
            data={"content": "test report"},
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_403_report_comment_by_self_check(self):
        response = self.client.post(
            reverse(
                "api-1.0.0:report_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            data={"content": "test report"},
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "You can't report yourself"})

    def test_fail_403_report_comment_by_banned_user(self):
        self.test_user_1.status = "banned"
        self.test_user_1.save()
        response = self.client.post(
            reverse(
                "api-1.0.0:report_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            data={"content": "test report"},
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_401_report_comment(self):
        response = self.client.post(
            reverse(
                "api-1.0.0:report_comment",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            data={"content": "test report"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})


class DeleteCommentFromDbTest(CommentTest):
    def test_success_delete_comment_from_db(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_comment_from_db",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        comment = Comment.objects.filter(id=self.test_post_comment.id)
        self.assertFalse(comment.exists())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_405_delete_comment_from_db(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:delete_comment_from_db",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_404_delete_comment_from_db_with_invalid_post_id(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_comment_from_db",
                kwargs={"post_id": 12345, "comment_id": self.test_post_comment.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_404_delete_comment_from_db_with_invalid_comment_id(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_comment_from_db",
                kwargs={"post_id": self.test_post.id, "comment_id": 12345},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_403_delete_comment_from_db_by_normal_user(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_comment_from_db",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_401_delete_comment_from_db(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_comment_from_db",
                kwargs={
                    "post_id": self.test_post.id,
                    "comment_id": self.test_post_comment.id,
                },
            ),
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})
