from ninja import Router, Form

from cores.schemas import NotFoundOut, SuccessOut, BadRequestOut
from comments.models import Comment, CommentReport
from comments.schemas import CreateCommentIn, CreateCommentReportIn, ModifyCommentIn
from users.auth import AuthBearer, has_authority, is_admin
from posts.models import Post

router = Router(tags=["댓글 관련 API"], auth=AuthBearer())

@router.post("/{post_id}/comments", response={200: SuccessOut, 400: BadRequestOut, 404: NotFoundOut})
def create_comment(request, post_id: int, body: CreateCommentIn = Form(...)):
    '''
    댓글 작성
    '''
    try:
        has_authority(request)
        Post.objects.get(id=post_id)
        Comment.objects.create(user_id=request.auth.id, post_id=post_id, content=body.content)

    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    return 200, {"message": "success"}

@router.delete("/{post_id}/comments/{comment_id}", response={200: SuccessOut, 400: BadRequestOut, 404: NotFoundOut})
def delete_comment(request, post_id: int, comment_id: int):
    '''
    댓글 삭제, DB삭제가 아니라 해당 댓글의 is_deleted 값만 True로 바꿈
    '''
    try:
        Post.objects.get(id=post_id)
        comment = Comment.objects.get(id=comment_id, is_deleted=False)
        has_authority(request, user_id=comment.user_id, user_check=True)
        comment.is_deleted = True
        comment.save()

    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    except Comment.DoesNotExist:
        return 404, {"message": "comment does not exist"}

    return 200, {"message": "success"}

@router.patch("/{post_id}/comments/{comment_id}", response={200: SuccessOut, 400: BadRequestOut, 404: NotFoundOut})
def modify_comment(request, post_id: int, comment_id: int, body: ModifyCommentIn):
    '''
    댓글 수정
    '''
    try:
        Post.objects.get(id=post_id, is_deleted=False)
        comment = Comment.objects.get(id=comment_id, post_id=post_id, is_deleted=False)
        has_authority(request, user_id=comment.user_id, user_check=True)
        comment.content = body.content
        comment.save()

    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    except Comment.DoesNotExist:
        return 404, {"message": "comment does not exist"}

    return 200, {"message": "success"}

@router.post("/{post_id}/comments/{comment_id}/report/", response={200: SuccessOut, 400: BadRequestOut, 404: NotFoundOut})
def report_comment(request, post_id: int, comment_id: int, body: CreateCommentReportIn = Form(...)):
    '''
    댓글 신고
    '''
    try:
        has_authority(request)
        Post.objects.get(id=post_id)
        Comment.objects.get(id=comment_id, is_deleted=False)
        CommentReport.objects.create(reporter_id=request.auth.id, comment_id=comment_id, content=body.content)

    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    except Comment.DoesNotExist:
        return 404, {"message": "comment does not exist"}

    return 200, {"message": "success"}

@router.delete("/{post_id}/comments/{comment_id}/delete/", response={200: SuccessOut, 400: BadRequestOut, 404: NotFoundOut})
def delete_comment_from_db(request, post_id: int, comment_id: int):
    '''
    댓글을 DB에서 삭제, 관리자만 가능
    '''
    try:
        is_admin(request)
        Post.objects.get(id=post_id)
        comment = Comment.objects.get(id=comment_id, is_deleted=False)
        comment.delete()

    except Post.DoesNotExist:
        return 404, {"message": "post does not exist"}

    except Comment.DoesNotExist:
        return 404, {"message": "comment does not exist"}

    return 200, {"message": "success"}