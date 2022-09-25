from django.db import models

from cores.models import TimeStampedModel

class ChatReport(TimeStampedModel):
    reporter_user = models.ForeignKey('users.user', related_name="chat_reporter", on_delete=models.CASCADE)
    reported_user = models.ForeignKey('users.user', related_name="chat_reported", on_delete=models.CASCADE)
    message_id    = models.CharField(max_length=30)
    message_text  = models.CharField(max_length=100)
    content       = models.CharField(max_length=500)
    is_checked    = models.BooleanField(default=False)

    class Meta:
        db_table = 'chat_report'

class MessageSaveTest(models.Model):
    message         = models.CharField(max_length=50)
    sender_nickname = models.CharField(max_length=10)
    sender_id       = models.IntegerField()
    room_id         = models.IntegerField()
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message_save_test'