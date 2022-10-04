from typing import List

from ninja import Schema, ModelSchema, Field

from comments.models import CommentReport
from posts.models import PostReport


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
