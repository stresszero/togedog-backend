from ninja import NinjaAPI

from users.api import router as users_router
from posts.api import router as posts_router
from comments.api import router as comments_router
from cores.api import router as cores_router
# from chat.api import router as chat_router

api = NinjaAPI(title="함께하개 API 문서", version="0.5.0")

api.add_router("/users", users_router)
api.add_router("/posts", posts_router)
api.add_router("/posts", comments_router)
api.add_router("/cores", cores_router)
# api.add_router("/chat", chat_router)

@api.get("/hello")
def hello(request):
    return {"hello": "world"}

@api.get("/notifications")
def get_notifications(request):
    return {"notifications": "notifications"}

# from users.auth import cookie_key


# @api.get("/cookiekey", auth=cookie_key)
# def cookie_test(request):
#     '''
#     쿠키 인가 테스트
#     '''
#     return f"Token = {request.auth}, {request.auth.id}, {request.auth.user_type}"
