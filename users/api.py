import jwt, requests
from pprint import pprint

from typing import List
from ninja import Router, Form

from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password, check_password

from users.schemas import EmailUserSignupIn, EmailUserSigninIn, ModifyUserIn, UserListOut, UserDetailOut
from cores.schemas import SuccessOut, AlreadyExistsOut, NotFoundOut, InvalidUserOut
from cores.models import UserAccountType, UserStatus
from cores.utils import generate_jwt, KakaoLoginAPI
from users.models import User
from users.auth import AuthBearer, is_admin, has_authority
from django.conf import settings

router = Router(tags=["사용자 관련 API"])

@router.get("/bearer", auth=AuthBearer())
def bearer(request):
    '''
    bearer 토큰 확인 테스트
    '''
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
    회원 탈퇴, 로그인한 본인 또는 관리자만 가능, DB에서 완전히 삭제됨
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
    사용자 비활성화, 관리자만 가능, 사용자의 status 값만 바뀜
    '''
    is_admin(request)
    user = User.objects.get(id=user_id)
    user.status = UserStatus.BANNED
    user.save()

    return 200, {"message": "success"}

@router.get("/login/kakao")
def kakao_login_get_code(request):
    '''
    카카오 로그인 창 띄우고 인가코드 받기
    users/login/kakao
    '''
    api_key      = settings.KAKAO_REST_API_KEY
    redirect_uri = settings.KAKAO_REDIRECT_URI
    auth_api     = "https://kauth.kakao.com/oauth/authorize?response_type=code"
    return redirect(f'{auth_api}&client_id={api_key}&redirect_uri={redirect_uri}')

@router.get("/login/kakao/redirect")
def kakao_login_get_profile(request, code: str):
    '''
    카카오 인가코드로 토큰 받고 사용자 프로필 조회하고 회원가입 또는 로그인하고 JWT 발급
    '''
    try:
        kakao_api = KakaoLoginAPI(client_id=settings.KAKAO_REST_API_KEY)

        kakao_api.get_kakao_token(request.GET.get('code'))
        kakao_profile = kakao_api.get_kakao_profile()

        user, is_created  = User.objects.get_or_create(
            social_account_id = kakao_profile['id'],
            defaults = {
                'email'        : kakao_profile['kakao_account']['email'],
                'nickname'     : kakao_profile['kakao_account']['profile']['nickname'],
                'thumbnail_url': kakao_profile['kakao_account']['profile']['thumbnail_image_url'],
                'account_type' : UserAccountType.KAKAO,
            }
        )
        access_token = jwt.encode({"user": user.id, "user_type": str(user.user_type)}, settings.SECRET_KEY, settings.ALGORITHM)
        return JsonResponse({'access_token': access_token}, status=200)

    except KeyError:
        return JsonResponse({'message': 'key error'}, status=400)

@router.get("/login/google")
def google_login_get_code(request):
    '''
    구글 로그인 창 띄우고 인가코드 받기
    users/login/google
    '''
    auth_api      = "https://accounts.google.com/o/oauth2/v2/auth"
    client_id     = settings.GOOGLE_CLIENT_ID
    redirect_uri  = settings.GOOGLE_REDIRECT_URI
    response_type = settings.GOOGLE_RESPONSE_TYPE
    scopes        = settings.GOOGLE_SCOPE
    return redirect(f'{auth_api}?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&scope={scopes}')

@router.get("/login/google/redirect")
def google_login_get_profile(request, code: str):
    '''
    구글 인가코드로 토큰 받고 사용자 프로필 조회하고 회원가입 또는 로그인하고 JWT 발급
    '''
    code = request.GET.get('code')
    google_token_api = "https://oauth2.googleapis.com/token"
    data = {
        "grant_type"   : "authorization_code",
        "code"         : code,
        "client_id"    : settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri" : settings.GOOGLE_REDIRECT_URI,
    }

    access_token = requests.post(google_token_api, data=data, timeout=3).json()['access_token']
    req_uri      = 'https://www.googleapis.com/oauth2/v3/userinfo'
    headers      = {'Authorization': f'Bearer {access_token}'}
    user_info    = requests.get(req_uri, headers=headers, timeout=3).json()

    user, is_created = User.objects.get_or_create(
            social_account_id = user_info["sub"],
            defaults = {
                "email"        : user_info["email"],
                "nickname"     : user_info["name"],
                "thumbnail_url": user_info["picture"],
                "account_type" : UserAccountType.GOOGLE,
            }
        )
    access_token = jwt.encode({"user": user.id, "user_type": str(user.user_type)}, settings.SECRET_KEY, settings.ALGORITHM)
    return JsonResponse({'access_token': access_token}, status=200)