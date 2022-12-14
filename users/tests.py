import json
import jwt
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.test import Client, TestCase
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
from django.urls import reverse

from cores.utils import create_user_login_response, generate_jwt
from users.models import User


class UserTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_user_1 = User.objects.create(
            name="테스트",
            nickname="테스트",
            email="test@test.com",
            user_type="normal",
            status="active",
            account_type="email",
            address="",
            created_at="2022-10-12T10:00:00Z",
        )
        self.test_admin = User.objects.create(
            name="admin",
            nickname="admin",
            email="admin@test.com",
            user_type="admin",
            status="active",
            account_type="email",
            address="",
            created_at="2022-10-12T10:00:00Z",
        )
        self.test_user_1.password = make_password(
            "test1234!!", salt=settings.PASSWORD_SALT
        )
        self.test_user_1.save()
        self.test_admin.password = make_password(
            "test1234@@", salt=settings.PASSWORD_SALT
        )
        self.test_admin.save()

        self.admin_user_login_response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": self.test_admin.email, "password": "test1234@@"}),
            content_type="application/json",
        )
        self.admin_jwt = self.admin_user_login_response.json()["access_token"]

        self.user_login_response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": self.test_user_1.email, "password": "test1234!!"}),
            content_type="application/json",
        )
        self.user_jwt = self.user_login_response.json()["access_token"]

    def tearDown(self):
        User.objects.all().delete()


class EmailUserSignupTest(UserTest):
    def test_success_email_user_signup(self):
        body = {
            "name": "홍길동",
            "nickname": "홍길동",
            "email": "mrhong@withdog.me",
            "password": "test1234!!",
            "address": "",
        }
        response = self.client.post(
            reverse("api-1.0.0:email_user_signup"),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_400_email_user_signup(self):
        body = {
            "name": "김철수",
            "nickname": "김철수",
            "email": "test@test.com",
            "password": "test123!@#",
            "address": "",
        }
        response = self.client.post(
            reverse("api-1.0.0:email_user_signup"),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"message": "user already exists"})

    def test_fail_422_email_user_signup(self):
        wrong_email_body = {
            "name": "테스터",
            "nickname": "테스터",
            "email": "test",
            "password": "test1234!!",
            "address": "",
        }
        wrong_email_response = self.client.post(
            reverse("api-1.0.0:email_user_signup"),
            json.dumps(wrong_email_body),
            content_type="application/json",
        )
        self.assertEqual(wrong_email_response.status_code, 422)

        bad_word_name_body = {
            "name": "fuck",
            "nickname": "테스터",
            "email": "asdf@asdf.com",
            "password": "test1234!!",
            "address": "",
        }
        bad_word_name_response = self.client.post(
            reverse("api-1.0.0:email_user_signup"),
            json.dumps(bad_word_name_body),
            content_type="application/json",
        )
        self.assertEqual(bad_word_name_response.status_code, 422)

        bad_word_nickname_body = {
            "name": "테스터",
            "nickname": "fuck",
            "email": "qwer@qwer.com",
            "password": "test1234!!",
            "address": "",
        }
        bad_word_nickname_response = self.client.post(
            reverse("api-1.0.0:email_user_signup"),
            json.dumps(bad_word_nickname_body),
            content_type="application/json",
        )
        self.assertEqual(bad_word_nickname_response.status_code, 422)

        invalid_password_body = {
            "name": "테스터",
            "nickname": "테스터",
            "email": "zxcv@zxcv.com",
            "password": "test1234",
            "address": "",
        }
        invalid_password_response = self.client.post(
            reverse("api-1.0.0:email_user_signup"),
            json.dumps(invalid_password_body),
            content_type="application/json",
        )
        self.assertEqual(invalid_password_response.status_code, 422)

    def test_fail_405_email_user_signup(self):
        response = self.client.get(reverse("api-1.0.0:email_user_signup"))
        self.assertContains(response, "Method not allowed", status_code=405)


class GetUserListTest(UserTest):
    def test_success_get_user_list(self):
        response = self.client.get(
            reverse("api-1.0.0:get_user_list") + "?date=2022-01-01~2022-12-31",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        results = {
            "items": [
                {
                    "id": self.test_admin.id,
                    "created_at": f"{self.test_admin.created_at.isoformat()[:-9]}Z",
                    "name": self.test_admin.name,
                    "nickname": self.test_admin.nickname,
                    "email": self.test_admin.email,
                    "user_type": self.test_admin.user_type,
                    "status": self.test_admin.status,
                    "account_type": self.test_admin.account_type,
                    "thumbnail_url": self.test_admin.thumbnail_url,
                    "mbti": self.test_admin.mbti,
                    "reported_count": 0,
                },
                {
                    "id": self.test_user_1.id,
                    "created_at": f"{self.test_user_1.created_at.isoformat()[:-9]}Z",
                    "name": self.test_user_1.name,
                    "nickname": self.test_user_1.nickname,
                    "email": self.test_user_1.email,
                    "user_type": self.test_user_1.user_type,
                    "status": self.test_user_1.status,
                    "account_type": self.test_user_1.account_type,
                    "thumbnail_url": self.test_user_1.thumbnail_url,
                    "mbti": self.test_user_1.mbti,
                    "reported_count": 0,
                },
            ],
            "count": User.objects.all().count(),
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    def test_fail_422_get_user_list_by_wrong_date_range(self):
        response = self.client.get(
            reverse("api-1.0.0:get_user_list") + "?date=2022-01-01_2022-12-31",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, "invalid date format", status_code=422)

    def test_fail_405_get_user_list(self):
        response = self.client.post(reverse("api-1.0.0:get_user_list"))
        self.assertContains(response, "Method not allowed", status_code=405)


class GetUserInfoTest(UserTest):
    def test_success_get_user_info_by_oneself(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:get_user_info",
                kwargs={"user_id": self.user_login_response.json()["user"]["id"]},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        results = {
            "id": self.test_user_1.id,
            "name": self.test_user_1.name,
            "nickname": self.test_user_1.nickname,
            "email": self.test_user_1.email,
            "user_type": self.test_user_1.user_type,
            "status": self.test_user_1.status,
            "account_type": self.test_user_1.account_type,
            "thumbnail_url": self.test_user_1.thumbnail_url,
            "mbti": self.test_user_1.mbti,
            "address": self.test_user_1.address,
            "created_at": f"{self.test_user_1.created_at.isoformat()[:-9]}Z",
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)
        self.assertEqual(str(self.test_user_1), "테스트")

    def test_fail_403_get_user_info(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:get_user_info",
                kwargs={"user_id": self.test_admin.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_401_get_user_info(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:get_user_info",
                kwargs={"user_id": self.test_user_1.id},
            ),
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})


class LogoutTest(UserTest):
    def test_success_logout(self):
        self.client.cookies["access_token"] = "test access token"
        self.client.cookies["refresh_token"] = "test refresh token"
        response = self.client.get(reverse("api-1.0.0:logout"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")
        self.assertEqual(response.json(), {"message": "cookie deleted"})

    def test_fail_405_logout(self):
        response = self.client.post(reverse("api-1.0.0:logout"))
        self.assertContains(response, "Method not allowed", status_code=405)


class DeactivateUserTest(UserTest):
    def test_success_deactivate_user(self):
        response = self.client.patch(
            reverse(
                "api-1.0.0:deactivate_user", kwargs={"user_id": self.test_user_1.id}
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(User.objects.get(id=self.test_user_1.id).status, "banned")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_403_deactivate_user(self):
        response = self.client.patch(
            reverse(
                "api-1.0.0:deactivate_user", kwargs={"user_id": self.test_user_1.id}
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_404_deactivate_user(self):
        response = self.client.patch(
            reverse("api-1.0.0:deactivate_user", kwargs={"user_id": 1234}),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_405_deactivate_user(self):
        response = self.client.get(
            reverse(
                "api-1.0.0:deactivate_user", kwargs={"user_id": self.test_user_1.id}
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertContains(response, "Method not allowed", status_code=405)


class CheckDuplicateEmailTest(UserTest):
    def test_success_check_duplicate_email(self):
        response = self.client.post(
            reverse("api-1.0.0:check_duplicate_email"),
            json.dumps({"email": "unique@test.com"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_400_check_duplicate_email(self):
        response = self.client.post(
            reverse("api-1.0.0:check_duplicate_email"),
            json.dumps({"email": "test@test.com"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"message": "email already exists"})

    def test_fail_422_check_duplicate_email(self):
        response = self.client.post(
            reverse("api-1.0.0:check_duplicate_email"),
            json.dumps({"email": "invalid"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 422)


class MainLoginCheckTest(UserTest):
    def test_success_main_login_check(self):
        response = self.client.post(
            reverse("api-1.0.0:main_login_check"),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 200)

    def test_fail_401_main_login_check(self):
        response = self.client.post(reverse("api-1.0.0:main_login_check"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})

    def test_fail_400_main_login_check(self):
        invalid_token_response = self.client.post(
            reverse("api-1.0.0:main_login_check"),
            HTTP_AUTHORIZATION="Bearer qwerasdfzxcv",
        )
        self.assertEqual(invalid_token_response.status_code, 400)
        self.assertEqual(invalid_token_response.json(), {"detail": "invalid token"})

    def test_fail_405_main_login_check(self):
        response = self.client.get(
            reverse("api-1.0.0:main_login_check"),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertContains(response, "Method not allowed", status_code=405)


class EmailUserLoginTest(UserTest):
    def test_success_email_user_login(self):
        data = {
            "access_token": self.user_jwt,
            "user": self.test_user_1.get_user_info_dict,
        }
        self.assertEqual(self.user_login_response.status_code, 200)
        self.assertEqual(self.user_login_response.json(), data)

    def test_fail_404_email_user_login(self):
        response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": "wrong@email.com", "password": "test1234!!"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_fail_400_email_user_login(self):
        response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": self.test_user_1.email, "password": "abcd"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"message": "invalid user"})

    def test_fail_405_email_user_login(self):
        response = self.client.get(reverse("api-1.0.0:email_user_login"))
        self.assertContains(response, "Method not allowed", status_code=405)


class DeleteUserAccountTest(UserTest):
    def test_success_delete_user_account(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_user_account", kwargs={"user_id": self.test_user_1.id}
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_401_delete_user_account(self):
        response = self.client.delete(
            reverse(
                "api-1.0.0:delete_user_account",
                kwargs={"user_id": self.test_user_1.id},
            ),
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})

    def test_fail_405_delete_user_account(self):
        response = self.client.put(
            reverse(
                "api-1.0.0:delete_user_account",
                kwargs={"user_id": self.test_user_1.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertContains(response, "Method not allowed", status_code=405)

    def test_fail_404_delete_user_account(self):
        response = self.client.delete(
            reverse("api-1.0.0:delete_user_account", kwargs={"user_id": 12345}),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})


class GetBannedUserListTest(UserTest):
    def test_success_get_banned_user_list(self):
        self.test_user_1.status = "banned"
        self.test_user_1.save()
        response = self.client.get(
            reverse("api-1.0.0:get_banned_user_list"),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        results = {
            "items": [
                {
                    "id": self.test_user_1.id,
                    "created_at": f"{self.test_user_1.created_at.isoformat()[:-9]}Z",
                    "name": self.test_user_1.name,
                    "nickname": self.test_user_1.nickname,
                    "email": self.test_user_1.email,
                    "user_type": self.test_user_1.user_type,
                    "status": self.test_user_1.status,
                    "account_type": self.test_user_1.account_type,
                    "thumbnail_url": self.test_user_1.thumbnail_url,
                    "mbti": self.test_user_1.mbti,
                    "reported_count": 0,
                }
            ],
            "count": 1,
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    def test_fail_401_get_banned_user_list(self):
        response = self.client.get(reverse("api-1.0.0:get_banned_user_list"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})

    def test_fail_405_get_banned_user_list(self):
        response = self.client.post(
            reverse("api-1.0.0:get_banned_user_list"),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertContains(response, "Method not allowed", status_code=405)


class ModifyUserInfoTest(UserTest):
    def test_success_without_file_modify_user_info(self):
        modify_data = {"name": "asdf", "nickname": "asdf"}
        response = self.client.patch(
            reverse(
                "api-1.0.0:modify_user_info", kwargs={"user_id": self.test_user_1.id}
            ),
            data=encode_multipart(data=modify_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        results = {
            "name_input": "asdf",
            "nickname_input": "asdf",
        }
        self.assertEqual(User.objects.get(id=self.test_user_1.id).name, "asdf")
        self.assertEqual(User.objects.get(id=self.test_user_1.id).nickname, "asdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    @patch("cores.utils.file_handler")
    def test_success_with_file_modify_user_info(self, mock_patch):
        upload_file = ContentFile(b"foo", "bar.png")
        modify_data = {"name": "asdf", "nickname": "asdf", "file": upload_file}

        mock_response = mock_patch.return_value
        mock_response.status_code = 200

        response = self.client.patch(
            reverse(
                "api-1.0.0:modify_user_info", kwargs={"user_id": self.test_user_1.id}
            ),
            data=encode_multipart(data=modify_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )

        mock_response.json.return_value = {
            "name_input": "asdf",
            "nickname_input": "asdf",
            "user_thumbnail_url": f"{User.objects.get(id=self.test_user_1.id).thumbnail_url}",
        }
        self.assertEqual(User.objects.get(id=self.test_user_1.id).name, "asdf")
        self.assertEqual(User.objects.get(id=self.test_user_1.id).nickname, "asdf")
        self.assertEqual(response.json(), mock_response.json.return_value)
        self.assertEqual(response.status_code, mock_response.status_code)

    def test_fail_400_modify_user_info(self):
        upload_file = ContentFile(b"foo", "foo.bar")
        modify_data = {"name": "asdf", "nickname": "asdf", "file": upload_file}
        wrong_extension_response = self.client.patch(
            reverse(
                "api-1.0.0:modify_user_info", kwargs={"user_id": self.test_user_1.id}
            ),
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
            reverse(
                "api-1.0.0:modify_user_info", kwargs={"user_id": self.test_user_1.id}
            ),
            data=encode_multipart(data=modify_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(too_large_file_response.status_code, 400)
        self.assertContains(
            too_large_file_response, "file size is too large", status_code=400
        )

    def test_fail_401_modify_user_info(self):
        modify_data = {"name": "asdf", "nickname": "asdf"}
        response = self.client.patch(
            reverse(
                "api-1.0.0:modify_user_info", kwargs={"user_id": self.test_admin.id}
            ),
            data=encode_multipart(data=modify_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})

    def test_fail_403_modify_user_info(self):
        response = self.client.patch(
            reverse(
                "api-1.0.0:modify_user_info", kwargs={"user_id": self.test_admin.id}
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_404_modify_user_info(self):
        response = self.client.patch(
            reverse("api-1.0.0:modify_user_info", kwargs={"user_id": 12345}),
            HTTP_AUTHORIZATION=f"Bearer {self.admin_jwt}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})


class KakaoSocialLoginTest(UserTest):
    @patch("cores.utils.requests")
    def test_success_kakao_social_login(self, mock_request):
        class FakeKakaoResponse:
            def json(self):
                return {
                    "id": 123456789,
                    "email": "qwer@qwer.com",
                    "kakao_account": {
                        "profile": {
                            "nickname": "QWER",
                            "thumbnail_image_url": "http://thumbnail.com/image.jpg",
                        },
                    },
                }

            @property
            def status_code(self):
                return 200

        mock_request.post = MagicMock(return_value=FakeKakaoResponse())
        response = self.client.post(
            reverse("api-1.0.0:kakao_social_login"),
            json.dumps({"token": "12345"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

    @patch("cores.utils.requests")
    def test_fail_400_kakao_social_login(self, mock_request):
        class KeyErrorResponse:
            def json(self):
                return {
                    "id": 123456789,
                    "email": "qwer@qwer.com",
                    "wrong_key": {
                        "profile": {
                            "nickname": "QWER",
                            "thumbnail_image_url": "http://thumbnail.com/image.jpg",
                        },
                    },
                }

            @property
            def status_code(self):
                return 200

        mock_request.post = MagicMock(return_value=KeyErrorResponse())
        response = self.client.post(
            reverse("api-1.0.0:kakao_social_login"),
            json.dumps({"token": "12345"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"message": "key error"})


class GoogleSocialLoginTest(UserTest):
    @patch("cores.utils.requests")
    def test_success_google_social_login(self, mock_request):
        class FakeGoogleResponse:
            def json(self):
                return {
                    "sub": 123456789,
                    "email": "qwer@qwer.com",
                    "given_name": "QWER",
                    "picture": "http://thumbnail.com/image.jpg",
                }

            @property
            def status_code(self):
                return 200

        mock_request.post = MagicMock(return_value=FakeGoogleResponse())
        response = self.client.post(
            reverse("api-1.0.0:google_social_login"),
            json.dumps({"token": "12345"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

    @patch("cores.utils.requests")
    def test_fail_400_google_social_login(self, mock_request):
        class KeyErrorResponse:
            def json(self):
                return {
                    "wrong_key": 123456789,
                    "email": "qwer@qwer.com",
                    "given_name": "QWER",
                    "picture": "http://thumbnail.com/image.jpg",
                }

            @property
            def status_code(self):
                return 200

        mock_request.post = MagicMock(return_value=KeyErrorResponse())
        response = self.client.post(
            reverse("api-1.0.0:google_social_login"),
            json.dumps({"token": "12345"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"message": "key error"})


class AuthBearerTest(UserTest):
    def test_success_auth_bearer(self):
        access_token = generate_jwt({"user": self.test_user_1.id}, "access")
        response = self.client.get(
            reverse("api-1.0.0:get_posts"),
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, 200)

    def test_fail_400_auth_bearer_user_does_not_exists(self):
        wrong_user_access_token = generate_jwt({"user": 12345}, "access")
        response = self.client.get(
            reverse("api-1.0.0:get_posts"),
            HTTP_AUTHORIZATION=f"Bearer {wrong_user_access_token}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "user does not exist"})

    def test_fail_400_auth_bearer_invalid_token(self):
        response = self.client.get(
            reverse("api-1.0.0:get_posts"),
            HTTP_AUTHORIZATION="Bearer 1234567890",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "invalid token"})

    def test_fail_401_auth_bearer_token_expired(self):
        payload = {
            "user": self.test_user_1.id,
            "exp": datetime.now(timezone.utc) + timedelta(seconds=1),
            "iat": datetime.now(timezone.utc),
        }
        expired_access_token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        time.sleep(2)
        response = self.client.get(
            reverse("api-1.0.0:get_posts"),
            HTTP_AUTHORIZATION=f"Bearer {expired_access_token}",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "token expired"})
