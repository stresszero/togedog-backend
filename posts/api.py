import uuid

from typing import List
from ninja import Router, File
from ninja.files import UploadedFile

from cores.schemas import NotFoundOut, SuccessOut, BadRequestOut
from cores.utils import s3_client
from posts.models import Post
from posts.schemas import GetPostOut
from users.auth import AuthBearer

router = Router(tags=["포스팅 관련 API"])

MB = 1024 * 1024

@router.get("/{post_id}", response={200: GetPostOut, 404: NotFoundOut}, auth=AuthBearer())
def get_post(request, post_id: int):
    '''
    포스팅 조회
    '''
    try:
        post = Post.objects.get(id=post_id, is_deleted=False)
        
    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    return 200, post

@router.get("", response={200: List[GetPostOut]}, auth=AuthBearer())
def get_post_list(request, offset: int = 0, limit: int = 9, sort: str = "-created_at"):
    '''
    포스팅 목록 조회, 기본 최신순정렬
    '''
    return 200, Post.objects.filter(is_deleted=False).order_by(sort)[offset:offset+limit]

@router.post("/upload/", response={200: SuccessOut, 400: BadRequestOut})
def upload_file(request, file: UploadedFile = File(...)):
    '''
    파일 업로드 테스트, 용량 50MB 제한
    '''
    upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
    if file.size > 50 * MB:
        return 400, {"message": "file size is too large"}
    s3_client.upload_fileobj(file, "post_images", upload_filename, ExtraArgs={"ACL": "public-read"})
    return 200, {"message": "success", "file_name": file.name}

# @router.post("/", response={200: SuccessOut, 400: BadRequestOut}, auth=AuthBearer())
# def create_post(request, title: str, content: str, file: UploadedFile = File(...)):
#     '''
#     포스팅 생성
#     '''
#     if file:
#         upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
#         if file.size > 50 * MB:
#             return 400, {"message": "file size is too large"}
#         s3_client.upload_fileobj(file, "post_images", upload_filename, ExtraArgs={"ACL": "public-read"})
#     else:
#         upload_filename = None
#     Post.objects.create(user=request.auth, title=title, content=content, image_url=upload_filename)
#     return 200, {"message": "success"}

# @router.patch("/{post_id}", response={200: SuccessOut, 400: BadRequestOut}, auth=AuthBearer())
# def modify_post(request, post_id: int, title: str, content: str, file: UploadedFile = File(...)):
#     '''
#     포스팅 수정
#     '''
#     try:
#         post = Post.objects.get(id=post_id, is_deleted=False)
        
#     except Post.DoesNotExist:
#         return 404, {"message": "post does not exist"}

#     if file:
#         upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
#         if file.size > 50 * MB:
#             return 400, {"message": "file size is too large"}
#         s3_client.upload_fileobj(file, "post_images", upload_filename, ExtraArgs={"ACL": "public-read"})
#         post.image_url = upload_filename
#     post.title = title
#     post.content = content
#     post.save()
#     return 200, {"message": "success"}

# @router.delete("/{post_id}", response={200: SuccessOut, 404: NotFoundOut}, auth=AuthBearer())
# def delete_post(request):
#     '''
#     포스팅 삭제, DB삭제가 아니라 is_deleted 값만 True로 바꿈
#     '''
#     try:
#         post = Post.objects.get(id=post_id, is_deleted=False)
        
#     except Post.DoesNotExist:
#         return 404, {"message": "post does not exist"}

#     post.is_deleted = True
#     post.save()
#     return 200, {"message": "success"}

# @router.post("/{post_id}", response={200: SuccessOut, 404: NotFoundOut}, auth=AuthBearer())
# def report_post(request):
#     '''
#     포스팅 신고
#     '''
#     pass
