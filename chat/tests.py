import json

from unittest.mock import patch

from django.urls import reverse

from .models import ChatReport
from users.tests import UserTest


class ChatTest(UserTest):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
        ChatReport.objects.all().delete()


class ReportChatMessageTest(ChatTest):
    @patch("chat.api.get_message")
    def test_success_report_chat_message(self, mock_patch):
        mock_patch.return_value = {"sender_id": 777}
        response = self.client.post(
            reverse("api-1.0.0:report_chat_message"),
            data=json.dumps(
                {
                    "reported_user_id": 999,
                    "message_id": "12345",
                    "message_text": "test message",
                    "content": "test content",
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        chat_report = ChatReport.objects.get(reporter_user_id=self.test_user_1.id)
        self.assertEqual(chat_report.reported_user_id, 999)
        self.assertEqual(chat_report.message_id, "12345")
        self.assertEqual(chat_report.message_text, "test message")
        self.assertEqual(chat_report.content, "test content")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    def test_fail_405_report_chat_message(self):
        response = self.client.get(
            reverse("api-1.0.0:report_chat_message"),
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "Method not allowed", status_code=405)

    @patch("chat.api.get_message")
    def test_fail_403_report_chat_message_by_self_check(self, mock_patch):
        mock_patch.return_value = {"sender_id": self.test_user_1.id}
        response = self.client.post(
            reverse("api-1.0.0:report_chat_message"),
            data=json.dumps(
                {
                    "reported_user_id": 999,
                    "message_id": "12345",
                    "message_text": "test message",
                    "content": "test content",
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "You can't report yourself"})

    @patch("chat.api.get_message")
    def test_fail_403_report_chat_message_by_banned_user(self, mock_patch):
        self.test_user_1.status = "banned"
        self.test_user_1.save()
        mock_patch.return_value = {"sender_id": 777}

        response = self.client.post(
            reverse("api-1.0.0:report_chat_message"),
            data=json.dumps(
                {
                    "reported_user_id": 999,
                    "message_id": "12345",
                    "message_text": "test message",
                    "content": "test content",
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "forbidden"})

    def test_fail_401_report_chat_message(self):
        response = self.client.post(
            reverse("api-1.0.0:report_chat_message"),
            data=json.dumps(
                {
                    "reported_user_id": 999,
                    "message_id": "12345",
                    "message_text": "test message",
                    "content": "test content",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Unauthorized"})

    @patch("chat.api.get_message")
    def test_fail_400_report_chat_message_by_no_message(self, mock_patch):
        mock_patch.return_value = False
        response = self.client.post(
            reverse("api-1.0.0:report_chat_message"),
            data=json.dumps(
                {
                    "reported_user_id": 999,
                    "message_id": "12345",
                    "message_text": "test message",
                    "content": "test content",
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.user_jwt}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"message": "message not found"})
