from datetime import datetime

from ninja import Schema, ModelSchema, Field

from comments.models import Comment


class CommentUser(Schema):
    id: int
    nickname: str
    created_at: datetime


class GetCommentOut(ModelSchema):
    user_id: int
    post_id: int
    user_nickname: str = Field(..., alias="user.nickname")
    user_thumbnail: str = Field(..., alias="user.thumbnail_url")

    class Config:
        model = Comment
        model_exclude = ["is_deleted", "user", "post", "updated_at"]
