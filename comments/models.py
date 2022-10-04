from django.db import models

from cores.models import TimeStampedModel


class Comment(TimeStampedModel):
    user = models.ForeignKey(
        "users.user", related_name="comments", on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        "posts.post", related_name="comments", on_delete=models.CASCADE
    )
    content = models.CharField(max_length=300, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "comment"


class CommentReport(TimeStampedModel):
    reporter_user = models.ForeignKey(
        "users.user", related_name="comment_reporter", on_delete=models.CASCADE
    )
    reported_user = models.ForeignKey(
        "users.user", related_name="comment_reported", on_delete=models.CASCADE
    )
    comment = models.ForeignKey(
        Comment, related_name="reports", on_delete=models.CASCADE
    )
    content = models.CharField(max_length=500)
    is_checked = models.BooleanField(default=False)

    class Meta:
        db_table = "comment_report"


class CommentDelete(TimeStampedModel):
    user = models.ForeignKey(
        "users.user", related_name="comment_deletes", on_delete=models.CASCADE
    )
    comment = models.ForeignKey(
        Comment, related_name="deletes", on_delete=models.CASCADE
    )
    delete_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "comment_delete"
