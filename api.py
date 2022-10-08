from typing import Union

from django.db.models import F, Q
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
from users.auth import AuthBearer, is_admin, cookie_key, auth_cookie
from users.models import UserTestCount


api = NinjaAPI(
    title="함께하개 API 문서", 
    version="1.0.0", 
    description="함께하개 프로젝트 API 명세서와 테스트 제공",
    # csrf=True,
    # docs_url="/api/docs",
)

api.add_router("/api/users", users_router)
api.add_router("/api/posts", posts_router)
api.add_router("/api/posts", comments_router)
api.add_router("/api/cores", cores_router)
api.add_router("/api/chat", chat_router)


@api.get(
    "/api/admin/notices",
    response=NoticeReportOut,
    auth=AuthBearer(),
    summary="신고 알람 건수와 목록 확인",
)
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


@api.post(
    "/api/admin/notices",
    response={200: MessageOut, 400: MessageOut},
    auth=AuthBearer(),
    summary="신고 건 확인 처리",
)
def check_notice(request, type: str, id: Union[str, int]):
    """
    게시글/댓글 신고 확인, 관리자만 가능
    - type이 post_report이고 id값이 정수이면 해당 게시글 신고 확인 처리
    - type이 comment_report이고 id값이 정수이면 해당 댓글 신고 확인
    - id가 all이면 모든 신고건(글/댓글) 확인 처리
    """
    is_admin(request)
    try:
        q = Q()
        q &= Q(is_checked=False)
        if id == "all":
            pass
        elif int(id):
            q &= Q(id=id)
        else:
            return 400, {"message": "bad request"}

        if type == "post_report":
            PostReport.objects.filter(q).update(
                is_checked=True, updated_at=timezone.now()
            )
        elif type == "comment_report":
            CommentReport.objects.filter(q).update(
                is_checked=True, updated_at=timezone.now()
            )
        else:
            return 400, {"message": "bad request"}

    except ValueError:
        return 400, {"message": "bad request"}

    return 200, {"message": "success"}


@api.get("/api/cookie/test", summary="쿠키 테스트")
def test_cookie(request):
    return {"cookie_access_token": request.COOKIES["access_token"]}


@api.post("/api/test-count", summary="MBTI 검사 횟수 올리기")
def add_test_count(request):
    count_obj = UserTestCount.objects.get(id=1)
    count_obj.test_count = F("test_count") + 1
    count_obj.save()
    count_obj.refresh_from_db()
    return {"message": "success"}


@api.get("/api/test-count", summary="MBTI 검사 횟수 확인")
def get_test_count(request):
    return {"userNum": UserTestCount.objects.get(id=1).test_count}


@api.get("/api/cookiekey", auth=auth_cookie)
def cookie_test(request):
    '''
    쿠키 인가 테스트
    '''
    return f"cookie_auth: {request.auth}, {request.auth.id}, {request.auth.user_type}"
