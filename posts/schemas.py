from datetime import datetime
from typing import List, Optional

from ninja import Schema, ModelSchema, Field, Form, File

from posts.models import Post, PostLike, PostReport
from comments.models import Comment

class PostUser(Schema):
    id: int
    nickname: str
    created_at: datetime

class GetCommentOut(ModelSchema):
    class Config:
        model = Comment
        model_exclude = ["is_deleted"]

class GetPostOut(ModelSchema):
    comments: List = Field(..., alias="comments.values")
    user_id: int = Field(..., alias="user.id")
    user_nickname: str = Field(..., alias="user.nickname")
    user_mbti: str = Field(..., alias='user.mbti')
    user_signup_time: Optional[datetime] = Field(..., alias='user.created_at')
    post_likes_count: int = Field(..., alias='likes.count')
    
    # @staticmethod
    # def resolve_time(obj):
    #     if not obj.user_signup_time:
    #         return
    #     return str(obj.user_signup_time)[0:5]

    class Config:
        model = Post
        model_exclude = ["user", "is_deleted"]
        
class CreatePostIn(ModelSchema):
    class Config:
        model = Post
        model_exclude = ["id", "user", "created_at", "updated_at", "image_url", "is_deleted"]

class CreatePostReportIn(ModelSchema):
    class Config:
        model = PostReport
        model_exclude = ["id", "reporter", "post", "created_at", "updated_at"]

class ModifyPostIn(Schema):
    subject: Optional[str]
    content: Optional[str]

class DeletePostIn(Schema):
    delete_reason: str = None

class DeletedPostOut(ModelSchema):
    user_nickname: str = Field(..., alias="user.nickname")
    user_mbti: str = Field(..., alias='user.mbti')

    class Config:
        model = Post
        model_fields = "__all__"

class AdminGetPostOut(Schema):
    id: int
    subject: str
    content: str
    image_url: Optional[str]
    user_id: int
    user_name: Optional[str] = Field(..., alias="user.name")
    user_nickname: str = Field(..., alias="user.nickname")
    user_email: str = Field(... ,alias="user.email")
    user_mbti: str = Field(..., alias='user.mbti')
    user_created_at: Optional[datetime] = Field(..., alias='user.created_at')

    class Config:
        model = Post
        model_exclude = ["is_deleted"]

class AdminGetDeletedPostOut(Schema):
    id: int
    subject: str
    content: str
    image_url: Optional[str]
    user_id: int
    user_name: Optional[str] = Field(..., alias="user.name")
    user_nickname: str = Field(..., alias="user.nickname")
    user_email: str = Field(... ,alias="user.email")
    user_mbti: str = Field(..., alias='user.mbti')
    user_created_at: Optional[datetime] = Field(..., alias='user.created_at')
    delete_reason: Optional[List] = Field(..., alias="get_delete_reason")

    class Config:
        model = Post
        model_exclude = ["is_deleted"]