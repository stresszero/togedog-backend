from django.db import models
from django.conf import settings

from cores.models import TimeStampedModel

class Post(TimeStampedModel):
    user       = models.ForeignKey('users.user', related_name="posts", on_delete=models.CASCADE)
    subject    = models.CharField(max_length=100, blank=True)
    content    = models.CharField(max_length=1000, blank=True)
    image_url  = models.CharField(max_length=500, blank=True, default=settings.DEFAULT_POST_IMAGE_URL)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'post'

    def __str__(self):
        return self.subject
    
    @property
    def get_delete_reason(self):
        return self.deletes.values_list('delete_reason', flat=True)

    @property
    def get_reports_count(self):
        return self.reports.count()

class PostLike(TimeStampedModel):
    like_user = models.ForeignKey('users.user', related_name="post_likes", on_delete=models.CASCADE)
    post      = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)

    class Meta:
        db_table = 'post_like'

class PostReport(TimeStampedModel):
    reporter_user = models.ForeignKey('users.user', related_name="post_reporter", on_delete=models.CASCADE)
    reported_user = models.ForeignKey('users.user', related_name="post_reported", on_delete=models.CASCADE)
    post          = models.ForeignKey(Post, related_name='reports', on_delete=models.CASCADE)
    content       = models.CharField(max_length=500)
    is_checked    = models.BooleanField(default=False)

    class Meta:
        db_table = 'post_report'

class PostDelete(TimeStampedModel):
    user          = models.ForeignKey('users.user', related_name="post_deletes", on_delete=models.CASCADE)
    post          = models.ForeignKey(Post, related_name='deletes', on_delete=models.CASCADE)
    delete_reason = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'post_delete'
