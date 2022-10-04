import jwt

from ninja.security import HttpBearer, APIKeyCookie
from ninja.errors import HttpError

from cores.models import UserStatus
from users.models import User
from django.conf import settings


def has_authority(
    request, user_id=None, user_check=False, banned_check=True, self_check=False
):
    """
    banned_check: 차단된 유저인지 확인할 경우 True, 아니면 False
    user_check: user_id가 있는 경우에 해당 유저가 로그인한 유저(request.auth)와
    같은지 확인, 관리자는 일치하지 않아도 통과
    인자로 request만 넣으면 차단된 유저 인지만 확인함
    self_check=True면 로그인한 유저가 자신의 댓글이나 글을 신고하는지 확인
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

        except User.DoesNotExist:
            return HttpError(400, "user does not exist")

        except jwt.ExpiredSignatureError:
            raise HttpError(401, "token expired")

        except jwt.DecodeError:
            raise HttpError(400, "invalid token")

        return self.user


class CookieKey(APIKeyCookie):
    param_name: str = "access_token"

    def authenticate(self, request, key):
        try:
            payload = jwt.decode(
                key, settings.SECRET_KEY, algorithms=settings.ALGORITHM
            )
            user = User.objects.get(id=payload["user"])

        except User.DoesNotExist:
            return HttpError(400, "user does not exist")

        except jwt.ExpiredSignatureError:
            raise HttpError(401, "token expired")

        except jwt.DecodeError:
            raise HttpError(400, "invalid token")

        return user


cookie_key = CookieKey()
