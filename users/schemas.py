import re
from datetime import datetime

from ninja import Schema, ModelSchema
from pydantic import EmailStr, validator

from users.models import User

REGEX_PASSWORD = "^(?=.*[A-Za-z])(?=.*\d)(?=.*[$@$!%*#?&])[A-Za-z\d$@$!%*#?&]{8,16}$"

class EmailUserSignupIn(Schema):
    nickname: str
    email: EmailStr
    password: str
    account_type: str = 'email'
    address: str = None

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
    name: str = None
    nickname: str
    email: EmailStr
    user_type: str
    status: str
    account_type: str
    thumbnail_url: str
    mbti: str

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
    name: str
    nickname: str
    address: str
    mbti: str
    thumbnail_url: str

# class ModifyUserIn(ModelSchema):
#     class Config:
#         model = User
#         model_fields = ['name', 'nickname', 'address', 'mbti', 'thumbnail_url']