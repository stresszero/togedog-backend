from django.db import models

from cores.models import TimeStampedModel, EnumField, UserType, UserStatus, UserAccountType

class User(TimeStampedModel):
    name              = models.CharField(max_length=50, null=True)
    nickname          = models.CharField(max_length=50)
    email             = models.CharField(max_length=100)
    password          = models.CharField(max_length=600, null=True)
    social_account_id = models.CharField(max_length=100, null=True, unique=True)
    user_type         = EnumField(enum=UserType, default=UserType.NORMAL, max_length=10)
    status            = EnumField(enum=UserStatus, default=UserStatus.ACTIVE, max_length=10)
    account_type      = EnumField(enum=UserAccountType, max_length=20)
    thumbnail_url     = models.CharField(max_length=500, default='http://thumbnail.url')
    address           = models.CharField(max_length=200, null=True)
    mbti              = models.CharField(max_length=4, default="none")

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.nickname
