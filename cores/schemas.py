import re
from typing import List

from django.conf import settings
from ninja import Field, ModelSchema, Schema
from pydantic import validator

from comments.models import CommentReport
from posts.models import PostReport
from users.models import NAME_AND_NICKNAME_MAX_LENGTH

REGEX_PASSWORD = "^(?=.*[A-Za-z])(?=.*\d)(?=.*[$@$!%*#?&])[A-Za-z\d$@$!%*#?&]{8,16}$"
REGEX_DATE_RANGE = "^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])~(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])"
REPORT_TYPES = ["post_report", "comment_report"]
SORT_TYPES = [
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "likes",
    "-likes",
]


def validate_name(value: str):
    if value in settings.BAD_WORDS_LIST:
        raise ValueError("name or nickname is not allowed")
    return (
        value
        if len(value) <= NAME_AND_NICKNAME_MAX_LENGTH
        else value[:NAME_AND_NICKNAME_MAX_LENGTH]
    )


def validate_filter_date(value: str):
    if re.match(REGEX_DATE_RANGE, value):
        return [value.split("~")[0], value.split("~")[1]]
    raise ValueError("invalid date format")


def validate_sort_types(value: str):
    if value in SORT_TYPES:
        return value
    raise ValueError("invalid sort type")


class ListFilters(Schema):
    reported_count__gte: int = Field(
        default=None, alias="reported", description="입력된 정수값 이상 신고받은 건만 검색"
    )
    created_at__date__range: str = Field(
        default=None, alias="date", description="사용자 가입일 또는 글 작성일 범위로 검색"
    )
    _validated_created_at__date__range = validator(
        "created_at__date__range", allow_reuse=True
    )(validate_filter_date)


class UserListFilters(ListFilters):
    nickname__icontains: str = Field(
        default=None, alias="search", description="사용자 닉네임 검색"
    )


class PostListFilters(ListFilters):
    user__nickname__icontains: str = Field(
        default=None, alias="search", description="글쓴이 닉네임 검색"
    )


class MessageOut(Schema):
    message: str


class ContentIn(Schema):
    content: str


class CommentReportOut(ModelSchema):
    comment_id: int = Field(..., alias="comment.id")
    post_id: int = Field(..., alias="comment.post_id")

    class Config:
        model = CommentReport
        model_fields = ["id", "content"]


class PostReportOut(ModelSchema):
    post_id: int = Field(..., alias="post.id")

    class Config:
        model = PostReport
        model_fields = ["id", "content"]


class NoticeReportOut(Schema):
    count: int = None
    post_reports: List[PostReportOut] = []
    comment_reports: List[CommentReportOut] = []


class CheckNoticeIn(Schema):
    id: str
    type: str

    @validator("id")
    def validate_report_id(cls, value):
        if value == "all":
            return None
        elif value.isdigit() and value != "0":
            return int(value)
        raise ValueError("invalid report id")

    @validator("type")
    def validate_report_type(cls, value):
        if value in REPORT_TYPES:
            return value
        raise ValueError("invalid report type")
