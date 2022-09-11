import jwt

from ninja.security import HttpBearer, APIKeyCookie
from ninja.errors import HttpError

from cores.models import UserStatus
from users.models import User
from django.conf import settings

def is_admin(request):
    if request.auth.user_type != "admin":
        raise HttpError(403, "forbidden")

def has_authority(request, user_id=None, user_check=False, banned_check=True):
    '''
    banned_check: 강퇴 유저인지 확인할 경우 True, 아니면 False
    user_check: user_id가 있는 경우에 해당 유저가 로그인한 유저(request.auth)와 
    같은지 확인, 관리자는 일치하지 않아도 통과
    '''
    if banned_check and request.auth.status == UserStatus.BANNED.value:
        raise HttpError(403, "forbidden")

    if user_check and user_id:
        if request.auth.user_type != "admin" and request.auth.id != user_id:
            raise HttpError(403, "forbidden")

def is_banned(request):
    if request.auth.status == UserStatus.BANNED.value:
        raise HttpError(403, "forbidden")

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM) 
            user = User.objects.get(id=payload["user"])

        except User.DoesNotExist:
            return HttpError(400, "user does not exist")

        except jwt.ExpiredSignatureError:
            raise HttpError(401, "token expired")

        except jwt.DecodeError:
            raise HttpError(400, "invalid token")

        return user

class CookieKey(APIKeyCookie):
    param_name: str = "access_token"

    def authenticate(self, request, key):
        try:
            payload = jwt.decode(key, settings.SECRET_KEY, algorithms=settings.ALGORITHM) 
            user = User.objects.get(id=payload["user"])

        except User.DoesNotExist:
            return HttpError(400, "user does not exist")

        except jwt.ExpiredSignatureError:
            raise HttpError(401, "token expired")

        except jwt.DecodeError:
            raise HttpError(400, "invalid token")

        return user

cookie_key = CookieKey()