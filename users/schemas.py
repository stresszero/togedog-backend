import re
from datetime import datetime
from typing import Optional

from ninja import Schema, ModelSchema, Field
from pydantic import EmailStr, validator

from users.models import User

REGEX_PASSWORD = "^(?=.*[A-Za-z])(?=.*\d)(?=.*[$@$!%*#?&])[A-Za-z\d$@$!%*#?&]{8,16}$"

class EmailSignupCheckIn(Schema):
    email: EmailStr

class EmailUserSignupIn(Schema):
    name: str
    nickname: str
    email: EmailStr
    password: str
    account_type: str = "email"
    address: Optional[str] 

    @validator('password')
    def validate_password(cls, value):
        if re.match(REGEX_PASSWORD, value):
            return value
        raise ValueError("invalid password")

class EmailUserSigninIn(Schema):
    email: EmailStr
    password: str

class UserListOut(Schema):
    id: int
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
    name: str = None
    nickname: str
    email: EmailStr
    user_type: str
    status: str
    account_type: str
    thumbnail_url: str
    mbti: str
    address: str = None
    created_at: datetime

class ModifyUserIn(Schema):
    name: Optional[str]
    nickname: Optional[str]
    mbti: Optional[str]

class TestKakaoToken(Schema):
    token: str

class ReportUserIn(Schema):
    content: str