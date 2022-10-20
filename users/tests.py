import json
import jwt
import os

from unittest.mock import patch, MagicMock

from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from ninja.testing import TestClient

from users.models import User
from users.schemas import UserDetailOut

# to avoid ConfigError when using ninja TestClient
os.environ["NINJA_SKIP_REGISTRY"] = "yes"

# user = User.objects.get(id=9)
# json.loads(json.dumps(UserDetailOut.from_orm(user).dict(), cls=DjangoJSONEncoder))

# list = (
#         User.objects.annotate(
#             reported_count=Count("post_reported", distinct=True)
#             + Count("comment_reported", distinct=True)
#         )
#         .filter(id__lte=50)
#         .order_by("-created_at")
#     )
# listout=[UserListOut.from_orm(i).dict() for i in list]
# json.loads(json.dumps(listout, cls=DjangoJSONEncoder))
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
        self.test_user_1.password = make_password("test1234!!", salt=settings.PASSWORD_SALT)
        self.test_user_1.save()
        self.test_admin.password = make_password("test1234@@", salt=settings.PASSWORD_SALT)
        self.test_admin.save()

    def tearDown(self):
        User.objects.all().delete()
    
    def test_success_email_user_signup(self):
        body = {
            "name": "테스터",
            "nickname": "테스터",
            "email": "tester@test.com",
            "password": "test1234!!",
            "address": "",
        }
        response = self.client.post(
            reverse("api-1.0.0:email_user_signup"),
            json.dumps(body), 
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_400_email_user_signup(self):
        body = {
            "name": "테스터",
            "nickname": "테스터",
            "email": "test@test.com",
            "password": "test1234!!",
            "address": "",
        }
        response = self.client.post(
            reverse("api-1.0.0:email_user_signup"),
            json.dumps(body), 
            content_type="application/json"
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
            content_type="application/json"
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
        self.assertEqual(response.status_code, 405)

    def test_success_get_user_list(self):
        admin_user_login_response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": self.test_admin.email, "password": "test1234@@"}),
            content_type="application/json"
        ).json()
        admin = User.objects.get(id=admin_user_login_response['user']['id'])

        admin_jwt = admin_user_login_response['access_token']
        response = self.client.get(
            reverse("api-1.0.0:get_user_list"), 
            HTTP_AUTHORIZATION=f'Bearer {admin_jwt}'
        )
        results = {
            "items": [
                {
                    "id": admin.id,
                    "created_at": f"{admin.created_at.isoformat()[:-9]}Z",
                    "name": admin.name,
                    "nickname": admin.nickname,
                    "email": admin.email,
                    "user_type": admin.user_type,
                    "status": admin.status,
                    "account_type": admin.account_type,
                    "thumbnail_url": settings.DEFAULT_USER_THUMBNAIL_URL,
                    "mbti": admin.mbti,
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
                    "thumbnail_url": settings.DEFAULT_USER_THUMBNAIL_URL,
                    "mbti": self.test_user_1.mbti,
                    "reported_count": 0,
                }
            ],
            "count": 2,
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    def test_fail_405_get_user_list(self):
        response = self.client.post(reverse("api-1.0.0:get_user_list"))
        self.assertContains(response, "Method not allowed", status_code=405)
        self.assertEqual(response.status_code, 405)

    def test_success_check_duplicate_email(self):
        response = self.client.post(
            reverse("api-1.0.0:check_duplicate_email"),
            json.dumps({"email": "testtest@test.com"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_400_check_duplicate_email(self):
        response = self.client.post(
            reverse("api-1.0.0:check_duplicate_email"),
            json.dumps({"email": "test@test.com"}), 
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"message": "email already exists"})
    
    def test_fail_422_check_duplicate_email(self):
        response = self.client.post(
            reverse("api-1.0.0:check_duplicate_email"),
            json.dumps({"email": "test"}), 
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 422)

    def test_success_get_user_info(self):
        user_login_response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": "test@test.com", "password": "test1234!!"}),
            content_type="application/json"
        ).json()
        user = User.objects.get(id=user_login_response['user']['id'])
        user_jwt = user_login_response['access_token']
        response = self.client.get(
            f"/api/users/{user.id}", 
            HTTP_AUTHORIZATION=f'Bearer {user_jwt}'
        )

        self.assertEqual(response.status_code, 200)

    def test_fail_403_get_user_info(self):
        user_login_response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": "test@test.com", "password": "test1234!!"}),
            content_type="application/json"
        ).json()
        user_jwt = user_login_response['access_token']
        response = self.client.get("/api/users/1234", HTTP_AUTHORIZATION=f'Bearer {user_jwt}')

        self.assertEqual(response.status_code, 403)

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
        self.assertEqual(response.status_code, 405)

    def test_success_deactivate_user(self):
        admin_user_login_response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": self.test_admin.email, "password": "test1234@@"}),
            content_type="application/json"
        ).json()
        admin_jwt = admin_user_login_response['access_token']

        response = self.client.patch(
                    reverse(
                        "api-1.0.0:deactivate_user", 
                        kwargs={"user_id": self.test_user_1.id}
                    ), 
                    HTTP_AUTHORIZATION=f'Bearer {admin_jwt}'
        )
        banned_user = User.objects.get(id=self.test_user_1.id)
        self.assertEqual(banned_user.status, "banned")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})
    
    def test_fail_403_deactivate_user(self):
        user_login_response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": "test@test.com", "password": "test1234!!"}),
            content_type="application/json"
        ).json()
        user_jwt = user_login_response['access_token']
        response = self.client.patch(
                    reverse(
                        "api-1.0.0:deactivate_user", 
                        kwargs={"user_id": self.test_user_1.id}
                    ), 
                    HTTP_AUTHORIZATION=f'Bearer {user_jwt}'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'detail': 'forbidden'})

    def test_fail_404_deactivate_user(self):
        admin_user_login_response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": self.test_admin.email, "password": "test1234@@"}),
            content_type="application/json"
        ).json()
        admin_jwt = admin_user_login_response['access_token']
        response = self.client.patch(
                    reverse(
                        "api-1.0.0:deactivate_user", 
                        kwargs={"user_id": 1234}
                    ), 
                    HTTP_AUTHORIZATION=f'Bearer {admin_jwt}'
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Not Found'})

    def test_fail_405_deactivate_user(self):
        admin_user_login_response = self.client.post(
            reverse("api-1.0.0:email_user_login"),
            json.dumps({"email": self.test_admin.email, "password": "test1234@@"}),
            content_type="application/json"
        ).json()
        admin_jwt = admin_user_login_response['access_token']
        response = self.client.get(
                    reverse(
                        "api-1.0.0:deactivate_user", 
                        kwargs={"user_id": self.test_user_1.id}
                    ), 
                    HTTP_AUTHORIZATION=f'Bearer {admin_jwt}'
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)
