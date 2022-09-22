import uuid

from typing import List
from django.conf import settings
from django.http import JsonResponse
from django.db.models import F, Q, Count
from django.shortcuts import get_object_or_404
from ninja import Router, Form
from ninja.pagination import paginate, PageNumberPagination
from ninja.files import UploadedFile

from cores.utils import s3_client
from users.auth import AuthBearer, has_authority, is_admin
from cores.schemas import NotFoundOut, SuccessOut, BadRequestOut
from posts.models import Post, PostLike, PostDelete, PostReport
from posts.schemas import (
    GetPostListOut, 
    CreatePostIn, 
    CreatePostReportIn,
    ModifyPostIn, 
    DeletedPostOut, 
    AdminGetPostOut, 
    DeletePostIn,
    AdminGetDeletedPostOut,
    AdminGetPostListOut
    )

router = Router(tags=["게시글 관련 API"], auth=AuthBearer())

MB = 1024 * 1024

@router.get("/admin", response=List[AdminGetPostListOut])
@paginate(PageNumberPagination, page_size=10)
def get_posts_by_admin(request, search: str = None, reported: int = None, date: str = None):
    '''
    관리자 페이지 게시글 조회, is_deleted=False인 글만 조회함,
    관리자 계정만 조회 가능하고 한페이지에 10개씩 조회,
    search: 사용자 닉네임으로 검색, reported: 신고건수 이상 글 조회(3입력하면 신고건수 3회 이상 글만 조회),
    date: 글 작성기간으로 검색(형식: 2021-01-01~2021-01-31, 중간에 ~으로 구분)
    '''
    is_admin(request)

    q = Q()
    if search:
        q &= Q(user__nickname__icontains=search)
    if reported:
        q &= Q(reported_count__gte=reported)
    if date:
        q &= Q(created_at__range=[date.split('~')[0], date.split('~')[1]])

    return Post.objects.annotate(reported_count=Count('reports', distinct=True))\
        .select_related('user').filter(q, is_deleted=False)\
        .prefetch_related('likes', 'reports').order_by('-created_at')

@router.get("/deleted/", response={200: List[DeletedPostOut]})
@paginate(PageNumberPagination, page_size=10)
def get_deleted_posts(request, search: str = None, date: str = None):
    '''
        삭제된 게시글 목록 조회, 관리자만 가능, search/date 파라미터 값 의미는 get posts by admin과 동일
    '''
    is_admin(request)

    q = Q()
    if search:
        q &= Q(user__nickname__icontains=search)
    if date:
        q &= Q(created_at__range=[date.split('~')[0], date.split('~')[1]])

    return Post.objects.select_related('user').filter(q, is_deleted=True)

@router.get("/deleted/{post_id}/", response={200: AdminGetDeletedPostOut, 404: NotFoundOut})
def get_deleted_post_by_admin(request, post_id: int):
    '''
        삭제된 게시글 상세조회, 삭제사유도 조회 가능, 관리자만 조회 가능
    '''
    try:
        is_admin(request)
        post = Post.objects.select_related('user').get(id=post_id, is_deleted=True)

    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    return 200, post

@router.get("/{post_id}")
def get_post(request, post_id: int):
    '''
    게시글 상세 조회, 게시글/댓글 모두 is_deleted=False인것만 나옴
    '''
    try:
        has_authority(request)
        post =  Post.objects.select_related('user').prefetch_related('likes').get(id=post_id, is_deleted=False)
        
        data = {
            "id"              : post.id,
            "user_id"         : post.user_id,
            "user_nickname"   : post.user.nickname,
            "user_thumbnail"  : post.user.thumbnail_url,
            "subject"         : post.subject,
            "content"         : post.content,
            "image_url"       : post.image_url,
            "created_at"      : post.created_at,
            "post_likes_count": post.likes.count(),
            "is_liked"        : True if post.likes.filter(like_user_id=request.auth.id).exists() else False,
            "comments"        : [
                comments for comments in post.comments.filter(is_deleted=False)
                .values('id', 'content', 'created_at', 'user_id', user_nickname=F("user__nickname"), user_thumbnail_url=F("user__thumbnail_url"))
                .order_by('created_at')
                ],
        }

    except Post.DoesNotExist:
        return JsonResponse({"message": "post does not exist"}, status=404)

    return data

@router.get("/{post_id}/admin/", response={200: AdminGetPostOut, 404: NotFoundOut})
def get_post_by_admin(request, post_id: int):
    '''
    관리자 페이지 용, 삭제 안된 정상 게시글 상세조회
    '''
    try:
        is_admin(request)
        post = Post.objects.select_related('user').get(id=post_id, is_deleted=False)

    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    return 200, post

@router.patch("/{post_id}/modify", response={200: SuccessOut, 400: BadRequestOut, 404: NotFoundOut})
def modify_post(request, post_id: int, body: ModifyPostIn = Form(...), file: UploadedFile = None):
    '''
    게시글 수정, 업로드 사진파일은 용량 50MB 제한
    '''
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    has_authority(request, user_id=post.user_id, user_check=True)

    if file:
        if file.size > 50 * MB:
            return 400, {"message": "file size is too large"}
        if post.image_url:
            s3_client.delete_object(Bucket="post_images", Key=post.image_url.split("/")[-1])

        upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
        s3_client.upload_fileobj(file, "post_images", upload_filename, ExtraArgs={"ACL": "public-read"})
        post.image_url = f'{settings.POST_IMAGES_URL}{upload_filename}'
        
    post.subject = body.subject
    post.content = body.content
    post.save()
    return 200, {"message": "success"}

@router.post("/{post_id}/delete/", response={200: SuccessOut, 404: NotFoundOut})
def delete_post(request, post_id: int, body: DeletePostIn = Form(...)):
    '''
    게시글 삭제, DB삭제가 아니라 해당 게시글의 is_deleted 값만 True로 바꿈, 관리자가 삭제하는 경우 삭제 사유 입력
    '''
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    has_authority(request, user_id=post.user_id, user_check=True)
    post.is_deleted = True
    post.save()
    delete_reason = "글쓴이 본인이 삭제" if post.user_id == request.auth.id else body.delete_reason
    PostDelete.objects.create(user_id=request.auth.id, post_id=post_id, delete_reason=delete_reason)

    return 200, {"message": "success"}

@router.post("/{post_id}/report/", response={200: SuccessOut})
def report_post(request, post_id: int, body: CreatePostReportIn = Form(...)):
    '''
    게시글 신고하기
    '''
    has_authority(request)
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    
    PostReport.objects.create(
        reporter_user_id=request.auth.id,
        reported_user_id=post.user_id, 
        post_id=post_id, 
        content=body.content
    )    
    return 200, {"message": "success"}

@router.delete("/{post_id}/delete/hard/", response={200: SuccessOut})
def delete_post_from_db(request, post_id: int):
    '''
    게시글을 DB에서 완전히 삭제(hard delete), 관리자만 가능
    '''
    is_admin(request)
    post = get_object_or_404(Post, id=post_id)
    post.delete()
        
    return 200, {"message": "success"}

@router.post("/{post_id}/like", response={200: SuccessOut, 404: NotFoundOut})
def like_post(request, post_id: int):
    '''
    게시글 좋아요(발도장), 이미 좋아요한 상태면 좋아요 취소
    '''
    try:    
        has_authority(request)
        Post.objects.get(id=post_id, is_deleted=False)
        like, is_liked = PostLike.objects.get_or_create(post_id=post_id, like_user_id=request.auth.id)
        if not is_liked:
            like.delete()
            return 200, {"message": "post like deleted"}

    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    return 200, {"message": "post like created"}

@router.get("", response={200: List[GetPostListOut]})
def get_posts(request, offset: int = 0, limit: int = 9, sort: str = "-created_at"):
    '''
    게시글 목록 조회, 한 페이지에 9개씩, 정렬(sort) 기본값 최신순(-created_at), 인기순(likes)
    is_deleted=False인 게시글만 나옴
    '''
    has_authority(request)
    return 200, Post.objects.filter(is_deleted=False).select_related('user').prefetch_related('likes').order_by(sort)[offset:offset+limit]

@router.post("", response={200: SuccessOut, 400: BadRequestOut})
def create_post(request, body: CreatePostIn = Form(...), file: UploadedFile = None):
    '''
    게시글 생성, 업로드 사진파일은 용량 50MB 제한
    '''
    has_authority(request)
    if file:
        if file.size > 50 * MB:
            return 400, {"message": "file size is too large"}
        upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
        s3_client.upload_fileobj(file, "post_images", upload_filename, ExtraArgs={"ACL": "public-read", "ContentType": file.content_type})
        upload_url = f'{settings.POST_IMAGES_URL}{upload_filename}'
    else:
        upload_url = None
    
    Post.objects.create(
        user_id=request.auth.id, 
        subject=body.subject, 
        content=body.content, 
        image_url=upload_url if upload_url else settings.DEFAULT_POST_IMAGE_URL,
    )
    
    return 200, {"message": "success"}