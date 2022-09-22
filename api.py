from typing import List
from ninja import NinjaAPI
from django.http import JsonResponse

from users.api import router as users_router
from users.auth import AuthBearer, is_admin
from posts.api import router as posts_router
from posts.models import PostReport
from comments.api import router as comments_router
from comments.models import CommentReport
from cores.api import router as cores_router
from cores.schemas import CommentReportOut, SuccessOut, NoticeReportOut

# from chat.api import router as chat_router

api = NinjaAPI(title="함께하개 API 문서", version="0.5.0")

api.add_router("/users", users_router)
api.add_router("/posts", posts_router)
api.add_router("/posts", comments_router)
api.add_router("/cores", cores_router)
# api.add_router("/chat", chat_router)

# @api.get("/hello")
# def hello(request):
#     return {"hello": "world"}

# @api.get("/notices")
# def get_notices(request, date: str, query: str):
#     print(date.split('~'))
#     return {"notices": "notices"}


@api.get("/admin/notices", response=NoticeReportOut, auth=AuthBearer())
def get_notices(request):
    """
    게시글/댓글 신고 미확인 건수(알람 숫자)와 목록 확인, 관리자만 가능
    """
    is_admin(request)
    post_reports = PostReport.objects.filter(is_checked=False)
    comment_reports = CommentReport.objects.filter(is_checked=False)

    return {
        "count": comment_reports.count() + post_reports.count(),
        "post_reports": list(post_reports),
        "comment_reports": list(comment_reports),
    }


@api.post("/admin/notices/all", response={200: SuccessOut}, auth=AuthBearer())
def check_all_notices(request):
    """
    게시글/댓글 신고 모두 확인처리(db에서 is_checked를 True로 바꿈), 관리자만 가능
    """
    is_admin(request)
    PostReport.objects.filter(is_checked=False).update(is_checked=True)
    CommentReport.objects.filter(is_checked=False).update(is_checked=True)
    return 200, {"message": "success"}


# @api.get("/cookietest")
# def test_cookie(request):
#     print(request.COOKIES)
#     return JsonResponse({'cookie_access_token': request.COOKIES['access_token']})

# from users.auth import cookie_key

# @api.get("/cookiekey", auth=cookie_key)
# def cookie_test(request):
#     '''
#     쿠키 인가 테스트
#     '''
#     return f"Token = {request.auth}, {request.auth.id}, {request.auth.user_type}"
