from datetime import datetime
from typing import List, Optional

from ninja import Schema, ModelSchema, Field

from posts.models import Post, PostReport
from comments.models import Comment

class PostUser(Schema):
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

class GetPostListOut(ModelSchema):
    user_id: int
    user_nickname: str = Field(..., alias="user.nickname")
    user_thumbnail: str = Field(..., alias="user.thumbnail_url")
    post_likes_count: int = Field(..., alias='likes.count')
    
    class Config:
        model = Post
        model_exclude = ["user", "is_deleted", "content"]

class AdminGetPostListOut(GetPostListOut):
    user_mbti: str = Field(..., alias='user.mbti')
    user_nickname: str = Field(..., alias="user.nickname")
    user_signup_time: datetime = Field(..., alias='user.created_at')
    reported_count: int 

class CreatePostIn(Schema):
    subject: str
    content: str

class ModifyPostIn(Schema):
    subject: Optional[str]
    content: Optional[str]

class DeletePostIn(Schema):
    delete_reason: Optional[str]

class DeletedPostOut(ModelSchema):
    user_nickname: str = Field(..., alias="user.nickname")
    user_mbti: str = Field(..., alias='user.mbti')

    class Config:
        model = Post
        model_fields = "__all__"

class GetPostOut(Schema):
    id: int
    user_id: int
    user_nickname: str = Field(..., alias="user.nickname")
    user_thumbnail: str = Field(..., alias="user.thumbnail_url")
    subject: str 
    content: str
    image_url: str
    created_at: datetime
    post_likes_count: int = Field(..., alias='get_likes_count')
    is_liked: bool
    comments_list: List[GetCommentOut]
    # comments: List[GetCommentOut] = Field(..., alias='get_comments_not_deleted')

    class Config:
        model = Post
        model_exclude = ["is_deleted"]

class AdminGetPostOut(Schema):
    id: int
    subject: str
    content: str
    created_at: datetime
    image_url: str
    user_id: int
    user_name: Optional[str] = Field(..., alias="user.name")
    user_nickname: str = Field(..., alias="user.nickname")
    user_email: str = Field(... , alias="user.email")
    user_mbti: str = Field(..., alias='user.mbti')
    user_address: str = Field(..., alias='user.address')
    user_thumbnail: str = Field(..., alias="user.thumbnail_url")
    user_created_at: Optional[datetime] = Field(..., alias='user.created_at')
    comments_list: List[GetCommentOut]
    # comments: Optional[List] = Field(..., alias='get_comments_not_deleted')

    class Config:
        model = Post

class AdminGetDeletedPostOut(Schema):
    id: int
    subject: str
    content: str
    created_at: datetime
    image_url: str
    user_id: int
    user_name: Optional[str] = Field(..., alias="user.name")
    user_nickname: str = Field(..., alias="user.nickname")
    user_email: str = Field(... , alias="user.email")
    user_mbti: str = Field(..., alias='user.mbti')
    user_address: str = Field(..., alias='user.address')
    user_thumbnail: str = Field(..., alias="user.thumbnail_url")
    user_created_at: Optional[datetime] = Field(..., alias='user.created_at')
    delete_reason: Optional[str] = Field(..., alias="get_delete_reason")

    class Config:
        model = Post

