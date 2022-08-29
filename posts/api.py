import uuid

from ninja import Router, File
from ninja.files import UploadedFile

from cores.schemas import NotFoundOut, SuccessOut, BadRequestOut
from cores.utils import s3_client
from posts.models import Post
from posts.schemas import GetPostOut

MB = 1024 * 1024

router = Router(tags=["포스팅 관련 API"])

@router.get("/{post_id}", response={200: GetPostOut, 404: NotFoundOut})
def read_post(request, post_id: int):
    try:
        post = Post.objects.get(id=post_id, is_deleted=False)
        
    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    return 200, post

@router.post("/upload/", response={200: SuccessOut, 400: BadRequestOut})
def upload_file(request, file: UploadedFile = File(...)):
    '''
    파일 업로드 테스트, 용량 50MB 제한
    '''
    print(file.name)
    print(file.size)
    upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
    if file.size > 50 * MB:
        return 400, {"message": "file size is too large"}
    s3_client.upload_fileobj(file, "post_images", upload_filename, ExtraArgs={"ACL": "public-read"})
    return 200, {"message": "success", "file_name": file.name}


