from ninja import Schema, ModelSchema

from posts.models import Post, PostLike

class GetPostOut(ModelSchema):
    class Config:
        model = Post
        model_exclude = ["is_deleted"]
        
# class GetPostListOut(ModelSchema):
#     class Config:
#         model = Post
#         model_exclude = ["is_deleted"]