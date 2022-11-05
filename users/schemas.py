import re
from datetime import datetime
from typing import Optional

from ninja import Schema
from pydantic import EmailStr, validator

from cores.schemas import REGEX_PASSWORD, validate_name
from users.models import User


class EmailSignupCheckIn(Schema):
    email: EmailStr


class EmailUserSigninIn(Schema):
    email: EmailStr
    password: str


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
