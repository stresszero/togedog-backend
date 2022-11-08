from enum import Enum

from django.db import models
from django.db.models import CharField


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# https://vixxcode.tistory.com/249
class EnumField(CharField):
    def __init__(self, enum, *args, **kwargs):
        """
        EnumField에 대한 값을 정의하지 않으면 해당 필드는
        TypeError를 내보내면서 반드시 정의하도록 요구
        """
        self.enum = enum
        super().__init__(*args, **kwargs)

    def get_default(self):
        """
        Django Field 메서드 오버라이딩
        enum값에 대한 validation을 하기 위해 오버라이딩 하였음
        """
        default = super().get_default()
        self.validate_enum(default)
        return default

    def to_python(self, value):
        """
        Django CharField 메서드 오버라이딩
        enum에 대한 value 체크 및 변환 작업을 위해 재정의
        """
        return super().to_python(self.validate_enum(value))

    def get_prep_value(self, value):
        return super().get_prep_value(self.validate_enum(value))

    def deconstruct(self):
        """
        enum이라는 파라미터를 추가하고 이를 사용하기 위해
        deconstruct 메소드의 kwargs에 해당 내용을 명시
        """
        name, path, args, kwargs = super().deconstruct()
        kwargs["enum"] = self.enum
        return name, path, args, kwargs

    def validate_enum(self, value):
        """
        애플리케이션에서 Enum 또는 해당되는 값을 넣었을 때에는 그 값을 반환하고
        그렇지 않았을 때에는 AttributeError를 일으킴
        """
        for name, member in self.enum.__members__.items():
            if member == value:
                return value.value
            if member.value == value:
                return value
        raise AttributeError("Not Found Enum Member")


class UserType(Enum):
    ADMIN = "admin"
    NORMAL = "normal"
    MANAGER = "manager"


class UserStatus(Enum):
    ACTIVE = "active"
    BANNED = "banned"


class UserAccountType(Enum):
    EMAIL = "email"
    KAKAO = "kakao"
    GOOGLE = "google"
