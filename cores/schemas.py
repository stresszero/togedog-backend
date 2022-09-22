from typing import List, Optional
from ninja import Schema, ModelSchema

from comments.models import CommentReport
from posts.models import PostReport

class MessageOut(Schema):
    message: str

class SuccessOut(Schema):
    message: str = "success"

class AlreadyExistsOut(Schema):
    message: str = 'already exists'

class NotFoundOut(Schema):
    message: str = 'not found'

class BadRequestOut(Schema):
    message: str = 'bad request'

class InvalidUserOut(Schema):
    message: str = 'invalid user'

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