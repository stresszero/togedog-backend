from typing import List

from ninja import Schema, ModelSchema

from comments.models import CommentReport
from posts.models import PostReport

class MessageOut(Schema):
    message: str

class CommentReportOut(ModelSchema):
    class Config:
        model = CommentReport
        model_fields = ["id", "content", "comment"]
    
class PostReportOut(ModelSchema):
    class Config:
        model = PostReport
        model_fields = ["id", "content", "post"]

class NoticeReportOut(Schema):
    count: int = None
    post_reports: List[PostReportOut] = []
    comment_reports: List[CommentReportOut] = []