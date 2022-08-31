import uuid

from typing import List
from ninja import Router, File, Form
from ninja.files import UploadedFile

from cores.schemas import NotFoundOut, SuccessOut, BadRequestOut
from cores.utils import s3_client
from posts.models import Post, PostReport, PostLike
from posts.schemas import GetPostOut, CreatePostIn, CreatePostReportIn
from users.auth import AuthBearer, has_authority, is_banned, is_admin

router = Router(tags=["게시글 관련 API"])

MB = 1024 * 1024

@router.get("/{post_id}", response={200: GetPostOut, 404: NotFoundOut}, auth=AuthBearer())
def get_post(request, post_id: int):
    '''
    게시글 하나 조회, is_deleted=False인것만 나옴
    '''
    try:
        is_banned(request)
        post = Post.objects.get(id=post_id, is_deleted=False)
        # post_comments = post.comments.exclude(is_deleted=True).values()
        
    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    return 200, post

@router.get("", response={200: List[GetPostOut]}, auth=AuthBearer())
def get_post_list(request, offset: int = 0, limit: int = 9, sort: str = "-created_at"):
    '''
    게시글 목록 조회, 한 페이지에 9개씩, 정렬 기본값 최신순(-created_at), is_deleted=False인것만 나옴
    '''
    is_banned(request)
    return 200, Post.objects.filter(is_deleted=False).order_by(sort)[offset:offset+limit]

@router.post("/upload/", response={200: SuccessOut, 400: BadRequestOut}, auth=AuthBearer())
def upload_file(request, file: UploadedFile = File(...)):
    '''
    파일 업로드 테스트, 용량 50MB 제한
    '''
    upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
    if file.size > 50 * MB:
        return 400, {"message": "file size is too large"}
    s3_client.upload_fileobj(file, "post_images", upload_filename, ExtraArgs={"ACL": "public-read"})
    return 200, {"message": "success", "file_name": file.name}

@router.post("/", response={200: SuccessOut, 400: BadRequestOut}, auth=AuthBearer())
def create_post(request, body: CreatePostIn = Form(...), file: UploadedFile = None):
    '''
    게시글 생성, 업로드 사진파일은 용량 50MB 제한
    '''
    is_banned(request)
    if file:
        if file.size > 50 * MB:
            return 400, {"message": "file size is too large"}
        upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
        s3_client.upload_fileobj(file, "post_images", upload_filename, ExtraArgs={"ACL": "public-read"})
        upload_url = f'https://togedog.s3.ap-northeast-2.amazonaws.com/post_images/{upload_filename}'
    else:
        upload_url = 'default_thumbnail_url'

    Post.objects.create(user_id=request.auth.id, subject=body.subject, content=body.content, image_url=upload_url)
    return 200, {"message": "success"}

@router.patch("/{post_id}", response={200: SuccessOut, 400: BadRequestOut}, auth=AuthBearer())
def modify_post(request, post_id: int, body: CreatePostIn = Form(...), file: UploadedFile = None):
    '''
    게시글 수정
    '''
    try:
        is_banned(request)
        post = Post.objects.get(id=post_id, user_id=request.auth.id, is_deleted=False)
        has_authority(request, post.user_id)
        
    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    if file:
        upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
        if file.size > 50 * MB:
            return 400, {"message": "file size is too large"}
        s3_client.upload_fileobj(file, "post_images", upload_filename, ExtraArgs={"ACL": "public-read"})
        s3_client.delete_object(Bucket="post_images", Key=post.image_url.split("/")[-1])
        post.image_url = upload_filename
    post.subject = body.subject
    post.content = body.content
    post.save()
    return 200, {"message": "success"}

@router.delete("/{post_id}", response={200: SuccessOut, 404: NotFoundOut}, auth=AuthBearer())
def delete_post(request, post_id: int):
    '''
    게시글 삭제, DB삭제가 아니라 해당 게시글의 is_deleted 값만 True로 바꿈
    '''
    try:
        post = Post.objects.get(id=post_id, is_deleted=False)
        
    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    is_banned(request)
    has_authority(request, post.user_id)
    post.is_deleted = True
    post.save()
    return 200, {"message": "success"}

@router.post("/{post_id}/report", response={200: SuccessOut, 404: NotFoundOut}, auth=AuthBearer())
def report_post(request, post_id: int, body: CreatePostReportIn = Form(...)):
    '''
    게시글 신고하기
    '''
    try:
        is_banned(request)
        post = Post.objects.get(id=post_id, is_deleted=False)
        
    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    PostReport.objects.create(reporter_id=request.auth.id, post_id=post_id, content=body.content)    
    return 200, {"message": "success"}

@router.delete("/{post_id}/delete", response={200: SuccessOut, 404: NotFoundOut}, auth=AuthBearer())
def delete_post_from_db(request, post_id: int):
    '''
    게시글을 DB에서 삭제, 관리자만 가능
    '''
    try:
        is_admin(request)
        post = Post.objects.get(id=post_id)
        post.delete()
        
    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    return 200, {"message": "success"}

@router.post("/{post_id}/like", response={200: SuccessOut, 404: NotFoundOut}, auth=AuthBearer())
def like_post(request, post_id: int):
    '''
    게시글 좋아요, 이미 좋아요한 상태면 좋아요 취소
    '''
    try:    
        is_banned(request)
        has_authority(request, request.auth.id)
        Post.objects.get(id=post_id, is_deleted=False)
        like, is_liked = PostLike.objects.get_or_create(post_id=post_id, like_user_id=request.auth.id)
        if not is_liked:
            like.delete()
            return 200, {"message": "post like deleted"}

    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    return 200, {"message": "post like created"}