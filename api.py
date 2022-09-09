from ninja import NinjaAPI, Schema, Form
from pydantic import EmailStr

from django.http import HttpResponse, JsonResponse

from users.models import User
from users.api import router as users_router
from posts.api import router as posts_router
from comments.api import router as comments_router
from cores.api import router as cores_router
# from chat.api import router as chat_router
from ninja.security import APIKeyCookie

api = NinjaAPI(title="Togedog API Document", version="0.5.0")

api.add_router("/users", users_router)
api.add_router("/posts", posts_router)
api.add_router("/posts", comments_router)
api.add_router("/cores", cores_router)
# api.add_router("/chat", chat_router)

@api.get("/hello")
def hello(request):
    # print(request.COOKIES.get('access_token')) 
    return {"hello": "world"}


