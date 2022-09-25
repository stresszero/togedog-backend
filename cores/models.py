from enum import Enum

from django.db import models
from django.db.models import CharField


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class UserType(Enum):
    ADMIN   = "admin"
    NORMAL  = "normal"
    MANAGER = "manager"

class UserStatus(Enum):
    ACTIVE = "active"
    BANNED = "banned"

class UserAccountType(Enum):
    EMAIL  = "email"
    KAKAO  = "kakao"
    GOOGLE = "google"

class EnumField(CharField):

    def __init__(self, enum, *args, **kwargs):
        self.enum = enum
        super().__init__(*args, **kwargs)

    def get_default(self):
        default = super().get_default()
        self.validate_enum(default)
        return default

    def to_python(self, value):
        return super().to_python(self.validate_enum(value))

    def get_prep_value(self, value):
        return super().get_prep_value(self.validate_enum(value))

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['enum'] = self.enum
        return name, path, args, kwargs

    def validate_enum(self, value):
        for name, member in self.enum.__members__.items():
            if member == value:
                return value.value
            if member.value == value:
                return value
        raise AttributeError('Not Found Enum Member')