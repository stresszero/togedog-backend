from datetime import datetime

from ninja import Schema, ModelSchema, Field

from comments.models import Comment, CommentReport

class CommentUser(Schema):
    id: int
    nickname: str
    created_at: datetime

class GetCommentOut(ModelSchema):

    class Config:
        model = Comment
        model_exclude = ["is_deleted"]

class CreateCommentIn(ModelSchema):

    class Config:
        model = Comment
        model_fields = ["content"]

class CreateCommentReportIn(ModelSchema):
    
        class Config:
            model = CommentReport
            model_fields = ["content"]

class ModifyCommentIn(Schema):
    content: str
    