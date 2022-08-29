from django.db import models

from cores.models import TimeStampedModel

class Post(TimeStampedModel):
    user       = models.ForeignKey('users.user', related_name="posts", on_delete=models.CASCADE)
    subject    = models.CharField(max_length=100, blank=True)
    content    = models.TextField()
    image_url  = models.CharField(max_length=500, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'post'

    def __str__(self):
        return self.subject

class PostLike(TimeStampedModel):
    like_user = models.ForeignKey('users.user', related_name="post_likes", on_delete=models.CASCADE)
    post      = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)

    class Meta:
        db_table = 'post_like'

class PostReport(TimeStampedModel):
    reporter = models.ForeignKey('users.user', related_name="post_reports", on_delete=models.CASCADE)
    post     = models.ForeignKey(Post, related_name='reports', on_delete=models.CASCADE)
    content  = models.CharField(max_length=500)

    class Meta:
        db_table = 'post_report'

