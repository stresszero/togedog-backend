from django.db import models
from django.conf import settings

from cores.models import TimeStampedModel, EnumField, UserType, UserStatus, UserAccountType

class User(TimeStampedModel):
    name              = models.CharField(max_length=10, null=True)
    nickname          = models.CharField(max_length=10)
    email             = models.CharField(max_length=100)
    password          = models.CharField(max_length=600, null=True)
    social_account_id = models.CharField(max_length=100, null=True, unique=True)
    user_type         = EnumField(enum=UserType, default=UserType.NORMAL.value, max_length=10)
    status            = EnumField(enum=UserStatus, default=UserStatus.ACTIVE.value, max_length=10)
    account_type      = EnumField(enum=UserAccountType, max_length=20)
    thumbnail_url     = models.CharField(max_length=500, default=settings.DEFAULT_USER_THUMBNAIL_URL)
    address           = models.CharField(max_length=20, null=True)
    mbti              = models.CharField(max_length=4, default="none")

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.nickname

class UserTestCount(models.Model):
    test_count = models.PositiveIntegerField()

    class Meta:
        db_table = 'user_test_count'