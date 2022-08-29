from django.db import models

from cores.models import TimeStampedModel

class Comment(TimeStampedModel):
    user       = models.ForeignKey('users.user', related_name='comments', on_delete=models.CASCADE)
    post       = models.ForeignKey('posts.post', related_name='comments', on_delete=models.CASCADE)
    content    = models.CharField(max_length=500, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'comment'

class CommentReport(TimeStampedModel):
    reporter = models.ForeignKey('users.user', related_name='comment_reports', on_delete=models.CASCADE)
    comment  = models.ForeignKey(Comment, related_name='reports', on_delete=models.CASCADE)
    content  = models.CharField(max_length=500)

    class Meta:
        db_table = 'comment_report'