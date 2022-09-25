from typing import List

from django.conf import settings
from django.db.models import F, Q, Count
from django.shortcuts import get_object_or_404
from ninja import Router, Form
from ninja.files import UploadedFile
from ninja.pagination import paginate, PageNumberPagination

from cores.utils import s3_client, validate_upload_file, handle_upload_file
from cores.schemas import MessageOut, ContentIn
from posts.models import Post, PostLike, PostDelete, PostReport
from posts.schemas import (
    GetPostListOut, 
    CreatePostIn, 
    ModifyPostIn, 
    DeletedPostOut, 
    AdminGetPostOut, 
    DeletePostIn,
    AdminGetDeletedPostOut,
    AdminGetPostListOut
    )
from users.auth import AuthBearer, has_authority, is_admin

router = Router(tags=["게시글 관련 API"], auth=AuthBearer())

MB = 1024 * 1024

@router.get("/admin", response=List[AdminGetPostListOut], summary="관리자 페이지 게시글 리스트 조회")
@paginate(PageNumberPagination, page_size=10)
def get_posts_by_admin(request, search: str = None, reported: int = None, date: str = None):
    '''
    **관리자 페이지 게시글 조회**
    - DB상에서 is_deleted=False인 글만 조회함
    - 관리자 계정만 조회 가능하고 한페이지에 10개씩 조회
    - search: 사용자 닉네임으로 검색
    - reported: 신고건수 이상 글 조회(3입력하면 신고건수 3회 이상 글만 조회)
    - date: 글 작성기간으로 검색(형식: 2021-01-01~2021-01-31, 중간에 ~으로 구분)
    '''
    is_admin(request)

    q = Q()
    if search:
        q &= Q(user__nickname__icontains=search)
    if reported:
        q &= Q(reported_count__gte=reported)
    if date:
        q &= Q(created_at__range=[date.split('~')[0], date.split('~')[1]])

    return Post.objects.annotate(reported_count=Count('reports', distinct=True)) \
        .select_related('user').filter(q, is_deleted=False)\
        .prefetch_related('likes', 'reports').order_by('-created_at')

@router.get("/deleted/", response={200: List[DeletedPostOut]}, summary="삭제된 게시글 리스트 조회")
@paginate(PageNumberPagination, page_size=10)
def get_deleted_posts(request, search: str = None, date: str = None):
    '''
    **삭제된 게시글 목록 조회, 관리자만 가능**
    - 파라미터 값 의미는 get posts by admin과 동일
    '''
    is_admin(request)

    q = Q()
    if search:
        q &= Q(user__nickname__icontains=search)
    if date:
        q &= Q(created_at__range=[date.split('~')[0], date.split('~')[1]])

    return Post.objects.select_related('user').filter(q, is_deleted=True)

@router.get("/deleted/{post_id}/", response={200: AdminGetDeletedPostOut}, summary="삭제된 게시글 상세조회")
def get_deleted_post_by_admin(request, post_id: int):
    '''
    삭제된 게시글 상세조회, 삭제사유도 조회 가능, 관리자만 조회 가능
    '''
    is_admin(request)

    return 200, get_object_or_404(Post.objects.select_related('user'), id=post_id, is_deleted=True)

@router.get("/{post_id}", summary="게시글 상세 조회")
def get_post(request, post_id: int):
    '''
    게시글 상세 조회
    - 게시글/댓글 모두 is_deleted=False인것만 나옴
    '''
    has_authority(request)
    post = get_object_or_404(Post.objects.select_related('user') \
        .prefetch_related('likes', 'comments'), id=post_id, is_deleted=False)
        
    return {
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
            .values('id', 'content', 'created_at', 'user_id', \
            user_nickname=F("user__nickname"), user_thumbnail_url=F("user__thumbnail_url"))
            .order_by('created_at')
        ],
    }

@router.patch("/{post_id}", response={200: MessageOut, 400: MessageOut}, summary="게시글 수정")
def modify_post(request, post_id: int, body: ModifyPostIn = Form(...), file: UploadedFile = None):
    '''
    게시글 수정, 업로드 사진파일은 용량 50MB 제한
    '''
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    has_authority(request, user_id=post.user_id, user_check=True)

    if validate_upload_file(file):
        if post.image_url != settings.DEFAULT_POST_IMAGE_URL:
            s3_client.delete_object(Bucket="post_images", Key=post.image_url.split("/")[-1])
        post.image_url = handle_upload_file(file, "post_images")
        
    post.subject = body.subject
    post.content = body.content
    post.save()
    return 200, {"message": "success"}

@router.get("/{post_id}/admin/", response={200: AdminGetPostOut}, summary="관리자 페이지에서 삭제 안된 정상 게시글 상세조회")
def get_post_by_admin(request, post_id: int):
    '''
    관리자 페이지 용, 삭제 안된 정상 게시글 상세조회
    '''
    is_admin(request)

    return 200, get_object_or_404(Post.objects.select_related('user')
    .prefetch_related('comments'), id=post_id, is_deleted=False)

@router.post("/{post_id}/delete/", response={200: MessageOut}, summary="게시글 삭제하기(soft delete)")
def delete_post(request, post_id: int, body: DeletePostIn = Form(...)):
    '''
    게시글 삭제
    - DB에서 삭제하는게 아니라 해당 게시글의 is_deleted 값만 True로 바꿈(soft delete)
    - 관리자가 삭제하는 경우 삭제 사유 입력
    '''
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    has_authority(request, user_id=post.user_id, user_check=True)
    post.is_deleted = True
    post.save()
    PostDelete.objects.create(
        user_id=request.auth.id, 
        post_id=post_id, 
        delete_reason="글쓴이 본인이 삭제" if post.user_id == request.auth.id else body.delete_reason
    )

    return 200, {"message": "success"}

@router.post("/{post_id}/report/", response={200: MessageOut}, summary="게시글 신고하기")
def report_post(request, post_id: int, body: ContentIn = Form(...)):
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

@router.delete("/{post_id}/delete/hard", response={200: MessageOut}, summary="게시글을 DB에서 완전히 삭제(hard delete)")
def delete_post_from_db(request, post_id: int):
    '''
    게시글을 DB에서 완전히 삭제(hard delete), 관리자만 가능
    '''
    is_admin(request)
    post = get_object_or_404(Post, id=post_id)
    if post.image_url != settings.DEFAULT_POST_IMAGE_URL:
        s3_client.delete_object(Bucket="post_images", Key=post.image_url.split("/")[-1])
    post.delete()
        
    return 200, {"message": "success"}

@router.post("/{post_id}/likes", response={200: MessageOut, 404: MessageOut}, summary="게시글 좋아요 또는 좋아요 취소")
def create_post_like(request, post_id: int):
    '''
    게시글 좋아요 생성, 사용자가 이미 해당 게시글을 좋아요한 상태면 좋아요 삭제
    '''
    has_authority(request)
    get_object_or_404(Post, id=post_id, is_deleted=False)

    like, is_liked = PostLike.objects.get_or_create(post_id=post_id, like_user_id=request.auth.id)
    if not is_liked:
        like.delete()
        return 200, {"message": "post like deleted"}

    return 200, {"message": "post like created"}

@router.get("", response={200: List[GetPostListOut]}, summary="게시글 목록 조회")
def get_posts(request, offset: int = 0, limit: int = 9, sort: str = "-created_at"):
    '''
    게시글 목록 조회, 한 페이지에 9개씩 
    - 정렬(sort) 기본값 최신순(-created_at), 인기순(likes)
    - DB상에서 is_deleted=False인 게시글만 나옴
    '''
    has_authority(request)
    return 200, Post.objects.filter(is_deleted=False).select_related('user') \
    .prefetch_related('likes').order_by(sort)[offset:offset+limit]

@router.post("", response={200: MessageOut, 400: MessageOut}, summary="게시글 작성하기")
def create_post(request, body: CreatePostIn = Form(...), file: UploadedFile = None):
    '''
    게시글 생성, 업로드 사진파일은 용량 50MB 제한
    '''
    has_authority(request)
    body_dict = body.dict()
    if validate_upload_file(file):
        body_dict['image_url'] = handle_upload_file(file, "post_images")

    Post.objects.create(user_id=request.auth.id, **body_dict)
    return 200, {"message": "success"}