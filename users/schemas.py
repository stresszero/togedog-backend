import re
from datetime import datetime
from typing import Optional

from ninja import Schema
from pydantic import EmailStr, validator, Field

from django.conf import settings
from users.models import User, NAME_AND_NICKNAME_MAX_LENGTH

REGEX_PASSWORD = "^(?=.*[A-Za-z])(?=.*\d)(?=.*[$@$!%*#?&])[A-Za-z\d$@$!%*#?&]{8,16}$"
REGEX_DATE_RANGE = '\d{4}-\d{2}-\d{2}~\d{4}-\d{2}-\d{2}'

def validate_name(value: str):
    if value in settings.BAD_WORDS_LIST:
        raise ValueError("name or nickname is not allowed")
    return value if len(value) <= NAME_AND_NICKNAME_MAX_LENGTH else value[:NAME_AND_NICKNAME_MAX_LENGTH]


class EmailSignupCheckIn(Schema):
    email: EmailStr


class EmailUserSignupIn(Schema):
    name: str
    nickname: str
    email: EmailStr
    password: str
    address: Optional[str]
    _validated_name = validator("name", allow_reuse=True)(validate_name)
    _validated_nickname = validator("nickname", allow_reuse=True)(validate_name)

    @validator("password")
    def validate_password(cls, value):
        if re.match(REGEX_PASSWORD, value):
            return value
        raise ValueError("invalid password")


class EmailUserSigninIn(Schema):
    email: EmailStr
    password: str


class UserListOut(Schema):
    id: int
    created_at: datetime
    name: Optional[str]
    nickname: str
    email: EmailStr
    user_type: str
    status: str
    account_type: str
    thumbnail_url: str
    mbti: str
    reported_count: int

    class Config:
        model = User


class UserDetailOut(Schema):
    id: int
    name: Optional[str]
    nickname: str
    email: EmailStr
    user_type: str
    status: str
    account_type: str
    thumbnail_url: str
    mbti: str
    address: Optional[str]
    created_at: datetime


class ModifyUserIn(Schema):
    name: Optional[str]
    nickname: Optional[str]
    mbti: Optional[str]
    _validated_name = validator("name", allow_reuse=True)(validate_name)
    _validated_nickname = validator("nickname", allow_reuse=True)(validate_name)


class TestKakaoToken(Schema):
    token: str

class UserListFilters(Schema):
    nickname__icontains: str = Field(None, alias="search", description="사용자 닉네임 검색")
    reported_count__gte: int = Field(None, alias="reported", description="정수값을 넣으면 해당 정수값 이상 신고받은 사용자 검색")
    created_at__date__range: str = Field(None, alias="date", description="사용자 가입일 범위로 검색")

    @validator("created_at__date__range")
    def validate_filter_date(cls, value):
        if re.match(REGEX_DATE_RANGE, value):
            return [value.split("~")[0], value.split("~")[1]]
        raise ValueError("invalid date format")
        
