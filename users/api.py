import requests
from typing import List

from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from ninja import Router, Form
from ninja.files import UploadedFile
from ninja.pagination import paginate, PageNumberPagination

from cores.models import UserAccountType, UserStatus
from cores.schemas import MessageOut
from cores.utils import generate_jwt, KakaoLoginAPI, s3_client, validate_upload_file, handle_upload_file
from users.auth import AuthBearer, is_admin, has_authority
from users.models import User
from users.schemas import (
    EmailUserSignupIn, 
    EmailUserSigninIn, 
    ModifyUserIn, 
    UserListOut, 
    UserDetailOut,
    EmailSignupCheckIn,
    TestKakaoToken,
    )

MB = 1024 * 1024

router = Router(tags=["사용자 관련 API"])

@router.get("", response=List[UserListOut], auth=[AuthBearer()], summary="관리자페이지 사용자 목록 조회")
@paginate(PageNumberPagination, page_size=10)
def get_user_list(request, search: str = None, reported: int = None, date: str= None):
    '''
    사용자 목록 조회
    - 관리자 계정만 조회 가능, 한페이지에 10개씩 조회
    - 쿼리 파라미터 search: 사용자 닉네임으로 검색
    - reported: 정수값을 넣으면 해당 정수값 이상 신고받은 사용자 검색
    - 리스폰스 객체
        - items: 유저정보 목록(배열)
        - count: 응답으로 나온 사용자의 전체 갯수
    '''
    is_admin(request)
    # for key, value in request.GET.items():
    #     print(key, value)
    q = Q()
    if search:
        q &= Q(nickname__icontains=search)
    if reported:
        q &= Q(reported_count__gte=reported)
    if date:
        q &= Q(created_at__range=[date.split('~')[0], date.split('~')[1]])

    return User.objects.annotate(
        reported_count = Count("post_reported", distinct=True) + Count("comment_reported", distinct=True)) \
        .filter(q).prefetch_related('post_reported', 'comment_reported')

@router.get("/bearer", auth=AuthBearer(), summary="Bearer 토큰 확인")
def check_bearer(request):
    '''
    Bearer 토큰 확인 테스트
    '''
    return {
        "user_id"    : request.auth.id,
        "user_type"  : request.auth.user_type,
        "user_status": request.auth.status,
        "accout_type": request.auth.account_type
    }

@router.post("/signup/emailcheck/", response={200: MessageOut, 400: MessageOut}, summary="이메일 회원가입 시 이메일 중복 확인")
def check_email(request, body: EmailSignupCheckIn):
    '''
    이메일 회원가입 시 이메일 중복 확인 
    - 중복이면 400 에러("message": "email already exists")
    '''
    if User.objects.filter(email=body.email, account_type=UserAccountType.EMAIL.value).exists():
        return 400, {"message": "email already exists"}
    return 200, {"message": "success"}

@router.post("/signup", response={200: MessageOut, 201: MessageOut, 400: MessageOut}, summary="이메일 사용자 회원가입")
def email_user_signup(request, body: EmailUserSignupIn):
    '''
    이메일 사용자 회원가입(application/json)
    - 중복이면 400 에러("message": "email already exists")
    - 이름이나 닉네임이 욕설이면 400 에러
    '''
    body_dict = body.dict()
    if body_dict['name'] in settings.BAD_WORDS_LIST or body_dict['nickname'] in settings.BAD_WORDS_LIST:
        return 400, {"message": "bad words in name or nickname"}

    if User.objects.filter(email=body_dict["email"], account_type=UserAccountType.EMAIL.value).exists():
        return 400, {"message": "user already exists"}

    body_dict.update({"password": make_password(body_dict["password"], salt=settings.PASSWORD_SALT)})
    User.objects.create(**body_dict)
    return 201, {"message": "success"}

@router.get("/{user_id}", response={200: UserDetailOut}, auth=[AuthBearer()], summary="사용자 정보 조회")    
def get_user_info(request, user_id: int):
    '''
    사용자 정보 조회, 로그인한 본인 계정 또는 관리자만 조회 가능
    '''
    has_authority(request, user_id, user_check=True, banned_check=False)
    
    return get_object_or_404(User, id=user_id)

@router.patch("/{user_id}", response={400: MessageOut}, auth=[AuthBearer()], summary="사용자 정보 수정")
def modify_user_info(request, user_id: int, body: ModifyUserIn = Form(...), file: UploadedFile = None):
    '''
    사용자 정보 수정, 로그인한 본인 계정 또는 관리자만 수정 가능
    '''
    has_authority(request, user_id, user_check=True, banned_check=False)
    user = get_object_or_404(User, id=user_id)

    body_dict = body.dict()
    if body_dict['name'] in settings.BAD_WORDS_LIST or body_dict['nickname'] in settings.BAD_WORDS_LIST:
        return 400, {"message": "bad words in name or nickname"}

    res = {}
    if validate_upload_file(file):
        if user.thumbnail_url != settings.DEFAULT_USER_THUMBNAIL_URL:
            s3_client.delete_object(Bucket="user_thumbnail", Key=user.thumbnail_url.split("/")[-1])
        user.thumbnail_url = handle_upload_file(file, "user_thumbnail")
        res["user_thumbnail_url"] = user.thumbnail_url

    for attr, value in body_dict.items():
        if value:
            setattr(user, attr, value)
            res[f'{attr}_input'] = value
    user.save()

    return JsonResponse(res)         

@router.delete("/{user_id}", response={200: MessageOut}, auth=[AuthBearer()], summary="회원 탈퇴")
def delete_user(request, user_id: int):
    '''
    회원 탈퇴, 로그인한 본인 또는 관리자만 가능, DB에서 완전히 삭제됨
    '''
    has_authority(request, user_id, user_check=True, banned_check=False)
    user = get_object_or_404(User, id=user_id)
    user.delete()

    return 200, {"message": "success"}

@router.patch("/{user_id}/ban", response={200: MessageOut}, auth=[AuthBearer()], summary="사용자 비활성화")
def deactivate_user(request, user_id: int):
    '''
    사용자 비활성화, 관리자만 가능
    - DB에서 사용자의 status 값이 banned로 바뀜
    '''
    is_admin(request)
    user = get_object_or_404(User, id=user_id)
    user.status = UserStatus.BANNED
    user.save()

    return 200, {"message": "success"}

# @router.get("/login/kakao")
# def kakao_login_get_code(request):
#     '''
#     카카오 로그인 창 띄우고 인가코드 받기
#     users/login/kakao
#     '''
#     api_key      = settings.KAKAO_REST_API_KEY
#     redirect_uri = settings.KAKAO_REDIRECT_URI
#     auth_api     = "https://kauth.kakao.com/oauth/authorize?response_type=code"
#     return redirect(f'{auth_api}&client_id={api_key}&redirect_uri={redirect_uri}')

# @router.get("/login/kakao/redirect")
# def kakao_login_get_profile(request, code: str):
#     '''
#     카카오 인가코드로 토큰 받고 사용자 프로필 조회하고 회원가입 또는 로그인하고 JWT 발급, 리프레시 토큰을 httponly 쿠키로 저장
#     '''
#     try:
#         kakao_api = KakaoLoginAPI(client_id=settings.KAKAO_REST_API_KEY)

#         kakao_api.get_kakao_token(request.GET.get('code'))
#         kakao_profile = kakao_api.get_kakao_profile()

#         user, is_created  = User.objects.get_or_create(
#             social_account_id = kakao_profile['id'],
#             defaults = {
#                 'email'        : kakao_profile['kakao_account']['email'],
#                 'nickname'     : kakao_profile['kakao_account']['profile']['nickname'],
#                 'thumbnail_url': kakao_profile['kakao_account']['profile']['thumbnail_image_url'],
#                 'account_type' : UserAccountType.KAKAO.value,
#             }
#         )
#         response = JsonResponse({'access_token': generate_jwt({"user": user.id}, "access")}, status=200)
#         response.set_cookie('refresh_token', generate_jwt({"user": user.id}, "refresh"), httponly=True, samesite="lax")
#         return response

#     except KeyError:
#         return JsonResponse({'message': 'key error'}, status=400)

# @router.get("/login/google")
# def google_login_get_code(request):
#     '''
#     구글 로그인 창 띄우고 인가코드 받기
#     users/login/google
#     '''
#     auth_api      = "https://accounts.google.com/o/oauth2/v2/auth"
#     client_id     = settings.GOOGLE_CLIENT_ID
#     redirect_uri  = settings.GOOGLE_REDIRECT_URI
#     response_type = settings.GOOGLE_RESPONSE_TYPE
#     scopes        = settings.GOOGLE_SCOPE
#     return redirect(f'{auth_api}?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&scope={scopes}')

# @router.get("/login/google/redirect")
# def google_login_get_profile(request, code: str):
#     '''
#     구글 인가코드로 토큰 받고 사용자 프로필 조회하고 회원가입 또는 로그인하고 JWT 발급, 리프레시 토큰을 httponly 쿠키로 저장
#     '''
#     code = request.GET.get('code')
#     google_token_api = "https://oauth2.googleapis.com/token"
#     data = {
#         "grant_type"   : "authorization_code",
#         "code"         : code,
#         "client_id"    : settings.GOOGLE_CLIENT_ID,
#         "client_secret": settings.GOOGLE_CLIENT_SECRET,
#         "redirect_uri" : settings.GOOGLE_REDIRECT_URI,
#     }
    
#     access_token = requests.post(google_token_api, data=data, timeout=3).json()['access_token']
#     req_uri      = 'https://www.googleapis.com/oauth2/v3/userinfo'
#     headers      = {'Authorization': f'Bearer {access_token}'}
#     user_info    = requests.get(req_uri, headers=headers, timeout=3).json()
#     print(user_info)
#     user, is_created = User.objects.get_or_create(
#             social_account_id = user_info["sub"],
#             defaults = {
#                 "email"        : user_info["email"],
#                 "nickname"     : user_info["given_name"],
#                 "thumbnail_url": user_info["picture"],
#                 "account_type" : UserAccountType.GOOGLE.value,
#             }
#         )
#     response = JsonResponse({'access_token': generate_jwt({"user": user.id}, "access")}, status=200)
#     response.set_cookie('refresh_token', generate_jwt({"user": user.id}, "refresh"), httponly=True, samesite="lax")
#     return response

@router.post("/login/email", response={200: MessageOut, 400: MessageOut, 404: MessageOut}, summary="이메일 사용자 로그인")
def email_user_login(request, body: EmailUserSigninIn):
    '''
    이메일 사용자 로그인(application/json)
    - 로그인 후 JWT 액세스 토큰 또는 리프레시 토큰을 httponly 쿠키로 저장
    '''
    body_dict = body.dict()
    user = get_object_or_404(User, email=body_dict['email'], account_type=UserAccountType.EMAIL)
        
    if check_password(body_dict["password"], user.password):
        data = {
            "access_token" : generate_jwt({"user": user.id}, "access"),
            "user": {
                "id"           : user.id,
                "name"         : user.name,
                "nickname"     : user.nickname,
                "email"        : user.email,
                "user_type"    : user.user_type,
                "status"       : user.status,
                "account_type" : user.account_type,
                "thumbnail_url": user.thumbnail_url,
                "mbti"         : user.mbti,
            }
        }
        response = JsonResponse(data, status=200)
        response.set_cookie('access_token', data["access_token"], httponly=True, samesite="None", secure=True)
        response.set_cookie('refresh_token', generate_jwt({"user": user.id}, "refresh"), httponly=True, samesite="None", secure=True)
        return response
        
    return 400, {"message": "invalid user"}

@router.get("/banned/all", response={200: List[UserListOut]}, auth=AuthBearer(), summary="차단 계정 목록 조회")
@paginate(PageNumberPagination, page_size=10)
def get_banned_user_list(request, search: str = None, date: str = None):
    '''
    차단 계정 목록 조회
    '''
    is_admin(request)

    q = Q()
    if search:
        q &= Q(nickname__icontains=search) | Q(email__icontains=search)
    if date:
        q &= Q(created_at__range=[date.split('~')[0], date.split('~')[1]])

    return User.objects.annotate(
        reported_count = Count("post_reported", distinct=True) + Count("comment_reported", distinct=True)
        ).filter(q, status=UserStatus.BANNED).prefetch_related('post_reported', 'comment_reported')

@router.post("/test/kakaotoken/", summary="카카오 로그인")
def kakao_token_test(request, token: TestKakaoToken):
    '''
    카카오 토큰 받아서 회원가입 또는 로그인
    '''
    kakao_response = requests.post(
            "https://kapi.kakao.com/v2/user/me",
            headers = {"Authorization": f"Bearer {token.token}"}, 
            timeout=3
        )
    if not kakao_response.status_code == 200:
        return JsonResponse({'message': 'invalid response'}, status=kakao_response.status_code)

    kakao_profile = kakao_response.json()
    kakao_nickname = kakao_profile['kakao_account']['profile']['nickname'] \
        if len(kakao_profile['kakao_account']['profile']['nickname']) <= 10 \
            else kakao_profile['kakao_account']['profile']['nickname'][:10]

    user, is_created  = User.objects.get_or_create(
        social_account_id = kakao_profile['id'],
        defaults = {
            'email'        : kakao_profile['kakao_account']['email'],
            'nickname'     : kakao_nickname,
            # 'thumbnail_url': kakao_profile['kakao_account']['profile']['thumbnail_image_url'],
            'account_type' : UserAccountType.KAKAO.value,
        }
    )
    data = {
        "access_token" : generate_jwt({"user": user.id}, "access"),
        "user": {
            "name"         : user.name,
            "nickname"     : user.nickname,
            "email"        : user.email,
            "user_type"    : user.user_type,
            "status"       : user.status,
            "account_type" : user.account_type,
            "thumbnail_url": user.thumbnail_url,
            "mbti"         : user.mbti,
        }
    }
    response = JsonResponse(data, status=200)
    response.set_cookie('access_token', data["access_token"], httponly=True, samesite="None", secure=True)
    response.set_cookie('refresh_token', generate_jwt({"user": user.id}, "refresh"), httponly=True, samesite="None", secure=True)
    return response

@router.post("/test/googletoken/", summary="구글 로그인")
def google_token_test(request, token: TestKakaoToken):
    '''
    구글 토큰 받아서 회원가입 또는 로그인
    '''
    req_uri     = 'https://www.googleapis.com/oauth2/v3/userinfo'
    headers     = {'Authorization': f'Bearer {token.token}'}
    user_info   = requests.get(req_uri, headers=headers, timeout=3).json()
    google_name = user_info["given_name"] if len(user_info["given_name"]) <= 10 else user_info["name"][:10]

    user, is_created = User.objects.get_or_create(
        social_account_id = user_info["sub"],
        defaults = {
            "email"        : user_info["email"],
            "nickname"     : google_name,
            "thumbnail_url": user_info["picture"],
            "account_type" : UserAccountType.GOOGLE.value,
        }
    )
    data = {
        "access_token" : generate_jwt({"user": user.id}, "access"),
        "user": {
            "name"         : user.name,
            "nickname"     : user.nickname,
            "email"        : user.email,
            "user_type"    : user.user_type,
            "status"       : user.status,
            "account_type" : user.account_type,
            "thumbnail_url": user.thumbnail_url,
            "mbti"         : user.mbti,
        }
    }
    response = JsonResponse(data, status=200)
    response.set_cookie('access_token', data["access_token"], httponly=True, samesite="None", secure=True)
    response.set_cookie('refresh_token', generate_jwt({"user": user.id}, "refresh"), httponly=True, samesite="None", secure=True)
    return response

# @router.get("/test/deletecookies")
# def delete_cookie(request):
#     '''
#     쿠키 삭제 테스트
#     '''
#     response = JsonResponse({'message': 'success'}, status=200)
#     response.delete_cookie('access_token')
#     response.delete_cookie('refresh_token')
#     return response