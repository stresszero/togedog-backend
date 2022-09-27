from django.db.models import F
from django.utils import timezone
from ninja import NinjaAPI

from chat.api import router as chat_router
from comments.api import router as comments_router
from comments.models import CommentReport
from cores.api import router as cores_router
from cores.schemas import MessageOut, NoticeReportOut
from posts.api import router as posts_router
from posts.models import PostReport
from users.api import router as users_router
from users.auth import AuthBearer, is_admin
from users.models import UserTestCount


api = NinjaAPI(title="함께하개 API 문서", version="0.9.0", 
description="함께하개 프로젝트 API 명세서와 테스트 제공")

api.add_router("/users", users_router)
api.add_router("/posts", posts_router)
api.add_router("/posts", comments_router)
api.add_router("/cores", cores_router)
api.add_router("/chat", chat_router)


@api.get("/admin/notices", response=NoticeReportOut, auth=AuthBearer(), summary="신고 알람 건수와 목록 확인")
def get_notices(request):
    """
    게시글/댓글 신고 미확인 건수(알람 숫자)와 목록 확인, 관리자만 가능
    """
    is_admin(request)
    post_reports = PostReport.objects.filter(is_checked=False)
    comment_reports = CommentReport.objects.filter(is_checked=False)

    return {
        "post_reports": list(post_reports),
        "comment_reports": list(comment_reports),
        "count": comment_reports.count() + post_reports.count(),
    }

@api.post("/admin/notices", response=MessageOut, auth=AuthBearer(), summary="신고 건 확인 처리")
def check_notice(request, id: int, type: str):
    """
    게시글/댓글 신고 확인, 관리자만 가능
    - type이 post_report면 게시글 신고 확인 
    - type이 comment_report면 댓글 신고 확인 
    - type이 all이면 모든 신고건 확인 처리, all이면 id값은 무시됨
    - id: 해당되는 type의 id값
    """
    is_admin(request)
    if type == "post_report":
        PostReport.objects.filter(id=id).update(is_checked=True, updated_at=timezone.now())

    if type == "comment_report":
        CommentReport.objects.filter(id=id).update(is_checked=True, updated_at=timezone.now())

    if type == "all":
        PostReport.objects.filter(is_checked=False).update(is_checked=True, updated_at=timezone.now())
        CommentReport.objects.filter(is_checked=False).update(is_checked=True, updated_at=timezone.now())
          
    return {"message": "success"}

@api.get("/cookie/test", summary="쿠키 테스트")
def test_cookie(request):
    print(request.COOKIES)
    return {'cookie_access_token': request.COOKIES['access_token']}

@api.post("/test-count", summary="MBTI 검사 횟수 올리기")
def add_test_count(request):
    count_obj = UserTestCount.objects.get(id=1)
    count_obj.test_count = F('test_count') + 1
    count_obj.save()
    count_obj.refresh_from_db()
    return {"message": "success"}

@api.get("/test-count", summary="MBTI 검사 횟수 확인")
def get_test_count(request):
    return {"userNum": UserTestCount.objects.get(id=1).test_count}

# from users.auth import cookie_key

# @api.get("/cookiekey", auth=cookie_key)
# def cookie_test(request):
#     '''
#     쿠키 인가 테스트
#     '''
#     return f"Token = {request.auth}, {request.auth.id}, {request.auth.user_type}"
