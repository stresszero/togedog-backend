from django.db import models
from django.conf import settings

from cores.models import TimeStampedModel, EnumField, UserType, UserStatus, UserAccountType

class User(TimeStampedModel):
    name              = models.CharField(max_length=10, null=True)
    nickname          = models.CharField(max_length=30)
    email             = models.CharField(max_length=100)
    password          = models.CharField(max_length=600, null=True)
    social_account_id = models.CharField(max_length=100, null=True, unique=True)
    user_type         = EnumField(enum=UserType, default=UserType.NORMAL, max_length=10)
    status            = EnumField(enum=UserStatus, default=UserStatus.ACTIVE, max_length=10)
    account_type      = EnumField(enum=UserAccountType, max_length=20)
    thumbnail_url     = models.CharField(max_length=500, default=settings.DEFAULT_USER_THUMBNAIL_URL)
    address           = models.CharField(max_length=20, null=True)
    mbti              = models.CharField(max_length=4, default="none")
    
    # @property
    # def reported_count(self):
    #     return self.post_reported.count() + self.comment_reported.count()

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.nickname

# class UserReport(TimeStampedModel):
    # reporter_user = models.ForeignKey(User, related_name='reporter', on_delete=models.CASCADE)
    # reported_user = models.ForeignKey(User, related_name='reported', on_delete=models.CASCADE)
    # content       = models.CharField(max_length=500)

#     class Meta:
#         db_table = 'user_report'