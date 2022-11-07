import jwt
from django.conf import settings
from ninja.errors import HttpError
from ninja.security import APIKeyCookie, HttpBearer

from cores.models import UserStatus
from users.models import User


def has_authority(
    request, user_id=None, user_check=False, banned_check=True, self_check=False
):
    """
    - banned_check: 차단된 유저를 확인하면 True(기본값), 아니면 False
    - 인자로 request만 넣으면 차단된 유저 인지만 확인함
    - user_check: user_id가 있는 경우에 해당 유저가 로그인한 유저(request.auth)와
    같은지 확인하면 True, 확인 안하면 False, 관리자는 일치하지 않아도 통과
    - self_check=True면 로그인한 유저가 자신의 댓글이나 글을 신고하는지 확인
    """
    if banned_check and request.auth.status == UserStatus.BANNED.value:
        raise HttpError(403, "forbidden")

    if self_check and request.auth.id == user_id:
        raise HttpError(403, "You can't report yourself")

    if (
        user_check
        and user_id
        and request.auth.user_type != "admin"
        and request.auth.id != user_id
    ):
        raise HttpError(403, "forbidden")


def is_admin(request):
    if request.auth.user_type != "admin":
        raise HttpError(403, "forbidden")


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
            )
            self.user = User.objects.get(id=payload["user"])

        except User.DoesNotExist as e:
            raise HttpError(400, "user does not exist") from e

        except jwt.ExpiredSignatureError as e:
            raise HttpError(401, "token expired") from e

        except jwt.DecodeError as e:
            raise HttpError(400, "invalid token") from e

        return self.user


class CheckAuthUserAdmin(AuthBearer):
    def authenticate(self, request, token):
        user = super().authenticate(request, token)
        if user.user_type != "admin":
            raise HttpError(403, "forbidden")
        return user


class CookieKey(APIKeyCookie):
    param_name: str = "access_token"

    def authenticate(self, request, key):
        try:
            payload = jwt.decode(
                key, settings.SECRET_KEY, algorithms=settings.ALGORITHM
            )
            self.user = User.objects.get(id=payload["user"])

        except User.DoesNotExist as e:
            raise HttpError(400, "user does not exist") from e

        except jwt.ExpiredSignatureError as e:
            raise HttpError(401, "token expired") from e

        except jwt.DecodeError as e:
            raise HttpError(400, "invalid token") from e

        return self.user


cookie_key = CookieKey()


def auth_cookie(request):
    cookie_type = "access_token"
    jwt_cookie = request.COOKIES.get(cookie_type)
    payload = jwt.decode(jwt_cookie, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
    return User.objects.get(id=payload["user"])
