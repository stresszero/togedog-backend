from django.conf import settings
from django.db import models

from cores.models import (EnumField, TimeStampedModel, UserAccountType,
                          UserStatus, UserType)

NAME_AND_NICKNAME_MAX_LENGTH = 10


class User(TimeStampedModel):
    name = models.CharField(max_length=NAME_AND_NICKNAME_MAX_LENGTH, null=True)
    nickname = models.CharField(max_length=NAME_AND_NICKNAME_MAX_LENGTH)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=600, null=True)
    social_account_id = models.CharField(max_length=100, null=True, unique=True)
    user_type = EnumField(enum=UserType, default=UserType.NORMAL.value, max_length=10)
    status = EnumField(enum=UserStatus, default=UserStatus.ACTIVE.value, max_length=10)
    account_type = EnumField(enum=UserAccountType, max_length=20)
    thumbnail_url = models.CharField(
        max_length=500, default=settings.DEFAULT_USER_THUMBNAIL_URL
    )
    address = models.CharField(max_length=20, blank=True)
    mbti = models.CharField(max_length=4, default="none")

    class Meta:
        db_table = "user"
        indexes = [
            models.Index(fields=["email"], name="user_email_idx"),
        ]

    @property
    def get_user_info_dict(self):
        return {
            "id"           : self.id,
            "name"         : self.name,
            "nickname"     : self.nickname,
            "email"        : self.email,
            "user_type"    : self.user_type,
            "status"       : self.status,
            "account_type" : self.account_type,
            "thumbnail_url": self.thumbnail_url,
            "mbti"         : self.mbti,
        }

    def __str__(self):
        return self.nickname


class UserTestCount(models.Model):
    test_count = models.PositiveIntegerField()

    class Meta:
        db_table = "user_test_count"
