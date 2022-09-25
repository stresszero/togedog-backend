from datetime import datetime

from ninja import Schema, ModelSchema

from comments.models import Comment

class CommentUser(Schema):
    id: int
    nickname: str
    created_at: datetime

class GetCommentOut(ModelSchema):

    class Config:
        model = Comment
        model_exclude = ["is_deleted"]
