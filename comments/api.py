from ninja import Router, Form

from django.shortcuts import get_object_or_404

from cores.schemas import MessageOut
from comments.models import Comment, CommentReport
from comments.schemas import CreateCommentIn, ModifyCommentIn, CreateCommentReportIn
from posts.models import Post
from users.auth import AuthBearer, has_authority, is_admin

router = Router(tags=["댓글 관련 API"], auth=AuthBearer())


@router.post(
    "/{post_id}/comments",
    response={200: MessageOut},
)
def create_comment(request, post_id: int, body: CreateCommentIn = Form(...)):
    """
    댓글 작성
    """
    has_authority(request)
    get_object_or_404(Post, id=post_id)
    Comment.objects.create(
            user_id=request.auth.id, post_id=post_id, content=body.content
    )

    return 200, {"message": "success"}

@router.delete(
    "/{post_id}/comments/{comment_id}",
    response={200: MessageOut},
)
def delete_comment(request, post_id: int, comment_id: int):
    """
    댓글 삭제, DB삭제가 아니라 해당 댓글의 is_deleted 값만 True로 바꿈
    """
    get_object_or_404(Post, id=post_id)

    comment = get_object_or_404(Comment, id=comment_id, is_deleted=False)
    has_authority(request, user_id=comment.user_id, user_check=True)
    comment.is_deleted = True
    comment.save()

    return 200, {"message": "success"}


@router.patch(
    "/{post_id}/comments/{comment_id}",
    response={200: MessageOut},
)
def modify_comment(request, post_id: int, comment_id: int, body: ModifyCommentIn):
    """
    댓글 수정
    """
    get_object_or_404(Post, id=post_id, is_deleted=False)
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id , is_deleted=False)
    has_authority(request, user_id=comment.user_id, user_check=True)
    comment.content = body.content
    comment.save()

    return 200, {"message": "success"}


@router.post(
    "/{post_id}/comments/{comment_id}/report/",
    response={200: MessageOut},
)
def report_comment(
    request, post_id: int, comment_id: int, body: CreateCommentReportIn = Form(...)
):
    """
    댓글 신고
    """
    has_authority(request)
    get_object_or_404(Post, id=post_id, is_deleted=False)
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id, is_deleted=False)
    CommentReport.objects.create(
            reporter_user_id=request.auth.id,
            reported_user_id=comment.user_id,
            comment_id=comment_id,
            content=body.content,
    )

    return 200, {"message": "success"}


@router.delete(
    "/{post_id}/comments/{comment_id}/delete/",
    response={200: MessageOut},
)
def delete_comment_from_db(request, post_id: int, comment_id: int):
    """
    댓글을 DB에서 삭제, 관리자만 가능
    """
    is_admin(request)
    get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id, is_deleted=False)
    comment.delete()

    return 200, {"message": "success"}
