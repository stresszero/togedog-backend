import json

from django.urls import reverse
from django.test import Client

from users.models import UserTestCount
from users.tests import UserTest
from posts.models import PostReport
from posts.tests import PostTest
from comments.models import CommentReport


class NoticeTest(PostTest):
    def setUp(self):
        super().setUp()
        self.test_post_report = PostReport.objects.create(
            reporter_user_id=self.test_admin.id,
            reported_user_id=self.test_user_1.id,
            post_id=self.test_post.id,
            content="test post report",
        )
        self.test_comment_report = CommentReport.objects.create(
            reporter_user_id=self.test_admin.id,
            reported_user_id=self.test_user_1.id,
            comment_id=self.test_post_comment.id,
            content="test comment report",
        )

    def tearDown(self):
        super().tearDown()
        PostReport.objects.all().delete()
        CommentReport.objects.all().delete()


class GetNoticesTest(NoticeTest):
    def test_success_get_notices(self):
        response = self.client.get(
            reverse("api-1.0.0:get_notices"),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        post_reports = PostReport.objects.filter(is_checked=False)
        comment_reports = CommentReport.objects.filter(is_checked=False)
        results = {
            "count": comment_reports.count() + post_reports.count(),
            "post_reports": [
                {
                    "id": post_report.id,
                    "content": post_report.content,
                    "post_id": post_report.post.id,
                }
                for post_report in post_reports
            ],
            "comment_reports": [
                {
                    "id": comment_report.id,
                    "content": comment_report.content,
                    "comment_id": comment_report.comment.id,
                    "post_id": comment_report.comment.post_id,
                }
                for comment_report in comment_reports
            ],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    def test_fail_405_get_notices(self):
        response = self.client.patch(
            reverse("api-1.0.0:get_notices"),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_403_get_notices_by_user(self):
        response = self.client.get(
            reverse("api-1.0.0:get_notices"),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_401_get_notices_by_anonymous(self):
        response = self.client.get(reverse("api-1.0.0:get_notices"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})


class CheckNoticeTest(NoticeTest):
    def test_success_check_notice(self):
        response = self.client.post(
            reverse("api-1.0.0:check_notice")
            + f"?id={self.test_post_report.id}"
            + "&type=post_report",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})
        self.assertTrue(PostReport.objects.get(id=self.test_post_report.id).is_checked)

        response = self.client.post(
            reverse("api-1.0.0:check_notice")
            + f"?id={self.test_comment_report.id}"
            + "&type=comment_report",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})
        self.assertTrue(
            CommentReport.objects.get(id=self.test_comment_report.id).is_checked
        )

    def test_success_check_notice_all_reports(self):
        response = self.client.post(
            reverse("api-1.0.0:check_notice") + "?id=all" + "&type=post_report",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})
        self.assertTrue(all(report.is_checked for report in PostReport.objects.all()))

        response = self.client.post(
            reverse("api-1.0.0:check_notice") + "?id=all" + "&type=comment_report",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})
        self.assertTrue(
            all(report.is_checked for report in CommentReport.objects.all())
        )

    def test_fail_422_check_notice_with_invalid_report_type(self):
        response = self.client.post(
            reverse("api-1.0.0:check_notice")
            + f"?id={self.test_post_report.id}"
            + "&type=foo",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, "invalid report type", status_code=422)

    def test_fail_422_check_notice_with_invalid_report_id(self):
        response = self.client.post(
            reverse("api-1.0.0:check_notice") + "?id=0" + "&type=post_report",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, "invalid report id", status_code=422)

        response = self.client.post(
            reverse("api-1.0.0:check_notice") + "?id=foo" + "&type=post_report",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, "invalid report id", status_code=422)

    def test_fail_405_check_notice(self):
        response = self.client.put(
            reverse("api-1.0.0:get_notices"),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_404_check_notice_by_user(self):
        response = self.client.post(
            reverse("api-1.0.0:check_notice") + "?id=12345" + "&type=post_report",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"message": "notices not found"})

    def test_fail_403_check_notice_by_user(self):
        response = self.client.post(
            reverse("api-1.0.0:check_notice")
            + f"?id={self.test_post_report.id}"
            + "&type=post_report",
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_401_check_notice(self):
        response = self.client.post(
            reverse("api-1.0.0:check_notice")
            + f"?id={self.test_post_report.id}"
            + "&type=post_report",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})


class TestCookie(UserTest):
    def setUp(self):
        super().setUp()
        self.test_cookie_client = Client()
        self.test_cookie_user_login_response = self.test_cookie_client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": self.test_user_1.email, "password": "test1234!!"}),
            content_type="application/json",
        )
        self.access_token = self.test_cookie_user_login_response.cookies[
            "access_token"
        ].value

    def tearDown(self):
        super().tearDown()

    def test_success_cookie_return_test(self):
        response = self.test_cookie_client.get(reverse("api-1.0.0:cookie_return_test"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"cookie_access_token": self.access_token})

    def test_fail_405_cookie_return_test(self):
        response = self.client.post(reverse("api-1.0.0:cookie_return_test"))
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_success_cookie_auth_test(self):
        self.test_cookie_client.cookies = self.test_cookie_user_login_response.cookies
        response = self.test_cookie_client.get(reverse("api-1.0.0:cookie_auth_test"))
        results = f"cookie_auth: {self.test_user_1.nickname}, {self.test_user_1.id}, {self.test_user_1.user_type}"
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    def test_fail_405_cookie_auth_test(self):
        self.test_cookie_client.cookies = self.test_cookie_user_login_response.cookies
        response = self.client.post(reverse("api-1.0.0:cookie_auth_test"))
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)


class MBTITestCountTest(UserTest):
    def setUp(self):
        super().setUp()
        UserTestCount.objects.create(id=1, test_count=0)

    def tearDown(self):
        super().tearDown()
        UserTestCount.objects.all().delete()

    def test_success_add_mbti_test_count(self):
        response = self.client.post(reverse("api-1.0.0:add_mbti_test_count"))
        self.assertEqual(UserTestCount.objects.get(id=1).test_count, 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_405_add_mbti_test_count(self):
        response = self.client.patch(reverse("api-1.0.0:add_mbti_test_count"))
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_success_get_mbti_test_count(self):
        response = self.client.get(reverse("api-1.0.0:get_mbti_test_count"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"userNum": UserTestCount.objects.get(id=1).test_count}
        )

        self.client.post(reverse("api-1.0.0:add_mbti_test_count"))
        response = self.client.get(reverse("api-1.0.0:get_mbti_test_count"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"userNum": UserTestCount.objects.get(id=1).test_count}
        )

    def test_fail_405_get_mbti_test_count(self):
        response = self.client.put(reverse("api-1.0.0:get_mbti_test_count"))
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)
