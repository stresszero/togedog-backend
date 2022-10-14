import json

from django.conf import settings
from django.test import TestCase, Client

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

    def tearDown(self):
        User.objects.all().delete()
    
    def test_success_email_user_signup(self):
        body = {
            "name": "테스터",
            "nickname": "테스터",
            "email": "tester@test.com",
            "password": "test1234!!",
            "account_type": "email",
            "address": "",
        }
        response = self.client.post(
            "/api/users/signup", 
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
            "account_type": "email",
            "address": "",
        }
        response = self.client.post(
            "/api/users/signup", 
            json.dumps(body), 
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"message": "user already exists"})

    def test_success_get_user_list(self):
        body = {
            "name": "admin",
            "nickname": "admin",
            "email": "admin@test.com",
            "password": "test1234!!",
            "account_type": "email",
            "address": "",
        }
        user_signup = self.client.post(
            "/api/users/signup", 
            json.dumps(body), 
            content_type="application/json"
        )
        user_login_response = self.client.post(
            "/api/users/login/email", 
            json.dumps({"email": body['email'], "password": body['password']}),
            content_type="application/json"
        ).json()
        user = User.objects.get(id=user_login_response['user']['id'])
        user.user_type = "admin"
        user.save()

        admin_jwt = user_login_response['access_token']
        response = self.client.get("/api/users", HTTP_AUTHORIZATION=f'Bearer {admin_jwt}')
        results = {
            "items": [
                {
                    "id": user.id,
                    "created_at": f"{user.created_at.isoformat()[:-9]}Z",
                    "name": user.name,
                    "nickname": user.nickname,
                    "email": user.email,
                    "user_type": user.user_type,
                    "status": user.status,
                    "account_type": user.account_type,
                    "thumbnail_url": settings.DEFAULT_USER_THUMBNAIL_URL,
                    "mbti": user.mbti,
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
                    "mbti": "none",
                    "reported_count": 0,
                }
            ],
            "count": 2,
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), results)

    def test_fail_405_get_user_list(self):
        response = self.client.post("/api/users")
        self.assertEqual(response.status_code, 405)