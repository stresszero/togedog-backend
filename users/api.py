import jwt

from typing import List
from ninja import Router, Form
from ninja.security import HttpBearer
from ninja.errors import HttpError
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404

from users.schemas import EmailUserSignupIn, EmailUserSigninIn, ModifyUserIn, UserListOut, UserDetailOut
from cores.schemas import SuccessOut, AlreadyExistsOut, NotFoundOut, InvalidUserOut
from cores.models import UserAccountType, UserStatus
from cores.utils import generate_jwt
from users.models import User
from django.conf import settings

router = Router(tags=["사용자 관련 API"])

def is_admin(request):
    if request.auth.user_type != "admin":
        raise HttpError(403, "forbidden")
    else:
        pass

def has_authority(request, user_id):
    if request.auth.user_type != "admin" and request.auth.id != user_id:
        raise HttpError(403, "forbidden")
    else:
        pass

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

@router.get("/hello")
def hello(request):
    return {"hello": "world"}

@router.get("/bearer", auth=AuthBearer())
def bearer(request):
    return {"user_id": request.auth.id, "user_type": request.auth.user_type}

# @router.post("/users/signup", response={201: SuccessOut})
# def email_user_signup_with_json(request, payload: EmailUserSignupIn):
#     '''
#     일반 사용자 회원가입(JSON)
#     '''
#     payload["password"] = make_password(payload["password"], salt=settings.PASSWORD_SALT)
#     User.objects.create(**payload.dict())
#     return 201, {"message": "success"}

@router.post("/signup", response={200: SuccessOut, 201: SuccessOut, 400: AlreadyExistsOut})
def email_user_signup_with_form(request, payload: EmailUserSignupIn=Form(...)):
    '''
    이메일 사용자 회원가입(Form)
    '''
    payload_dict = payload.dict()
    if User.objects.filter(email=payload_dict["email"], account_type=UserAccountType.EMAIL).exists():
        return 400, {"message": "user already exists"}

    payload_dict.update({"password": make_password(payload_dict["password"], salt=settings.PASSWORD_SALT)})
    User.objects.create(**payload_dict)
    return 201, {"message": "success"}

@router.post("/login", response={200: SuccessOut, 400: NotFoundOut, 404: InvalidUserOut})
def email_user_login_with_form(request, payload: EmailUserSigninIn=Form(...)):
    '''
    이메일 사용자 로그인(Form)
    로그인 후 JWT 발급
    '''
    payload_dict = payload.dict()
    try:
        user = User.objects.get(email=payload_dict["email"], account_type=UserAccountType.EMAIL)

        if check_password(payload_dict["password"], user.password):
            payload  = {"user": user.id, "user_type": user.user_type}
            response = JsonResponse({'access_token': generate_jwt(payload, "access")}, status=200)
            response.set_cookie('refresh_token', generate_jwt(payload, "refresh"), httponly=True, samesite="lax")
            return response
        else: 
            return 404, {"message": "invalid user"}
    
    except User.DoesNotExist:
        return 404, {"message": "user does not exist"}

@router.get("", response=List[UserListOut], auth=[AuthBearer()])
def get_user_list(request):
    '''
    사용자 목록 조회, 관리자 계정만 조회 가능
    '''
    is_admin(request)
    return User.objects.all()
    
@router.get("/{user_id}", response=UserDetailOut, auth=[AuthBearer()])    
def get_user_info(request, user_id: int):
    '''
    사용자 정보 조회, 로그인한 본인 계정 또는 관리자만 조회 가능
    '''
    has_authority(request, user_id)

    return User.objects.get(id=user_id)

@router.patch("/{user_id}", response={200: SuccessOut}, auth=[AuthBearer()])
def modify_user_info(request, user_id: int, payload: ModifyUserIn):
    '''
    사용자 정보 수정, 로그인한 본인 계정 또는 관리자만 수정 가능
    '''
    has_authority(request, user_id)
    user = User.objects.get(id=user_id)

    for attr, value in payload.dict().items():
        setattr(user, attr, value)
    user.save()

    return 200, {"message": "success"}

@router.delete("/{user_id}", response={200: SuccessOut}, auth=[AuthBearer()])
def delete_user(request, user_id: int):
    '''
    회원 탈퇴, 로그인한 본인 또는 관리자만 가능
    '''
    try:
        user = User.objects.get(id=user_id)
        has_authority(request, user_id)
        user.delete()

    except User.DoesNotExist:
        return 404, {"message": "user does not exist"}

    return 200, {"message": "success"}

@router.patch("/{user_id}/ban", response={200: SuccessOut}, auth=[AuthBearer()])
def deactivate_user(request, user_id: int):
    '''
    사용자 비활성화, 관리자만 가능
    '''
    is_admin(request)
    user = User.objects.get(id=user_id)
    user.status = UserStatus.BANNED
    user.save()

    return 200, {"message": "success"}
