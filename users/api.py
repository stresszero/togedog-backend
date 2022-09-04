from typing import List

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ninja import Form, Query
from ninja.router import URLBugFixedRouter
from ninja.files import UploadedFile
from ninja.pagination import paginate, PageNumberPagination

from cores.models import UserAccountType, UserStatus
from cores.schemas import MessageOut, UserListFilters
from cores.utils import (
    validate_upload_file,
    delete_existing_image,
    handle_upload_file,
    create_user_login_response,
    SocialLoginUserProfile,
)
from users.auth import AuthBearer, is_admin, has_authority
from users.models import User, NAME_AND_NICKNAME_MAX_LENGTH
from users.schemas import (
    EmailUserSignupIn,
    EmailUserSigninIn,
    ModifyUserIn,
    UserListOut,
    UserDetailOut,
    EmailSignupCheckIn,
    TestKakaoToken,
)

# https://github.com/vitalik/django-ninja/issues/575
router = URLBugFixedRouter(tags=["사용자 관련 API"])


@router.get(
    "", response=List[UserListOut], auth=[AuthBearer()], summary="관리자페이지 사용자 목록 조회"
)
@paginate(PageNumberPagination, page_size=10)
def get_user_list(request, query: UserListFilters = Query(...)):
    """
    사용자 목록 조회
    - 관리자 계정만 조회 가능, 한페이지에 10개씩 조회
    - 쿼리 파라미터
        - search: 사용자 닉네임 검색
        - reported: 정수를 넣으면 그 값 이상 신고받은 사용자 검색
        - date: "2022-01-01~2022-12-31" 형식으로 넣으면 사용자 가입일의 범위로 검색
        - page: 1부터 시작하는 페이지네이션 번호
    - 리스폰스
        - items: 사용자 상세정보 목록(배열), 10개씩 페이지네이션 됨
        - 기본값으로 가입일 최신 순으로 정렬됨
        - count: 결과로 나온 사용자 정보의 전체 개수
    """
    is_admin(request)
    user_filters = {key: value for key, value in query.dict().items() if value}

    return (
        User.objects.annotate(
            reported_count=Count("post_reported", distinct=True)
            + Count("comment_reported", distinct=True)
        )
        .filter(**user_filters)
        .order_by("-created_at")
    )


@router.get("/logout", summary="로그아웃")
def logout(request):
    """
    로그아웃 후 쿠키 삭제
    """
    response = JsonResponse({"message": "cookie deleted"}, status=200)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.post(
    "/signup/emailcheck/",
    response={200: MessageOut, 400: MessageOut},
    summary="이메일 회원가입 시 이메일 중복 확인",
)
def check_duplicate_email(request, body: EmailSignupCheckIn):
    """
    이메일 회원가입 시 이메일 중복 확인
    - 이메일 중복이면 400 에러("message": "email already exists")
    """
    if User.objects.filter(
        email=body.email, account_type=UserAccountType.EMAIL.value
    ).exists():
        return 400, {"message": "email already exists"}
    return 200, {"message": "success"}


@router.post(
    "/signup", response={200: MessageOut, 400: MessageOut}, summary="이메일 사용자 회원가입"
)
def email_user_signup(request, body: EmailUserSignupIn):
    """
    이메일 사용자 회원가입(application/json)
    - 이메일 중복이면 400 에러("message": "email already exists")
    - 이름이나 닉네임이 욕설이면 422 에러
    """
    body_dict = body.dict()
    if User.objects.filter(
        email=body_dict["email"], account_type=UserAccountType.EMAIL.value
    ).exists():
        return 400, {"message": "user already exists"}
    body_dict.update(
        {
            "password": make_password(body_dict["password"], salt=settings.PASSWORD_SALT),
            "account_type": UserAccountType.EMAIL.value,
        }
    )
    User.objects.create(**body_dict)
    return 200, {"message": "success"}


@router.get(
    "/{user_id}",
    response={200: UserDetailOut},
    auth=[AuthBearer()],
    summary="사용자 정보 조회",
)
def get_user_info(request, user_id: int):
    """
    사용자 정보 조회, 로그인한 본인 계정 또는 관리자만 조회 가능
    """
    has_authority(request, user_id, user_check=True, banned_check=False)
    return get_object_or_404(User, id=user_id)


@router.patch(
    "/{user_id}",
    response={400: MessageOut},
    auth=[AuthBearer()],
    summary="사용자 정보 수정",
)
def modify_user_info(
    request,
    user_id: int,
    body: ModifyUserIn = Form(...),
    file: UploadedFile = None,
):
    """
    사용자 정보 수정, 로그인한 본인 계정 또는 관리자만 수정 가능
    """
    has_authority(request, user_id, user_check=True, banned_check=False)
    user = get_object_or_404(User, id=user_id)

    body_dict = body.dict()
    res = {}

    if validate_upload_file(file):
        delete_existing_image(user.thumbnail_url, "user_thumbnail")
        user.thumbnail_url = handle_upload_file(file, "user_thumbnail")
        res["user_thumbnail_url"] = user.thumbnail_url

    for attr, value in body_dict.items():
        if value and hasattr(user, attr):
            setattr(user, attr, value)
            res[f"{attr}_input"] = value

    user.save()
    return JsonResponse(res, status=200)


@router.delete(
    "/{user_id}", response={200: MessageOut}, auth=[AuthBearer()], summary="회원 탈퇴"
)
def delete_user_account(request, user_id: int):
    """
    회원 탈퇴, 로그인한 본인 또는 관리자만 가능, DB에서 완전히 삭제됨
    """
    has_authority(request, user_id, user_check=True, banned_check=False)
    user = get_object_or_404(User, id=user_id)
    user.delete()

    return 200, {"message": "success"}


@router.patch(
    "/{user_id}/ban",
    response={200: MessageOut},
    auth=[AuthBearer()],
    summary="사용자 비활성화",
)
def deactivate_user(request, user_id: int):
    """
    사용자 비활성화, 관리자만 가능
    - DB에서 사용자의 status 값이 banned로 바뀜
    """
    is_admin(request)
    user = get_object_or_404(User, id=user_id)
    user.status = UserStatus.BANNED.value
    user.save()

    return 200, {"message": "success"}


@router.post(
    "/login/check",
    response={200: UserDetailOut, 400: MessageOut},
    auth=AuthBearer(),
    summary="메인페이지 로그인 상태 확인",
)
def main_login_check(request):
    """
    메인페이지에서 이미 로그인돼있는 상태인지 확인(쿠키 활용)
    """
    return 200, request.auth


@router.post(
    "/login/email",
    response={200: MessageOut, 400: MessageOut, 404: MessageOut},
    summary="이메일 사용자 로그인",
)
def email_user_login(request, body: EmailUserSigninIn):
    """
    이메일 사용자 로그인(application/json)
    - 로그인 후 JWT 액세스 토큰 또는 리프레시 토큰을 httponly 쿠키로 저장
    """
    body_dict = body.dict()
    user = get_object_or_404(
        User, email=body_dict["email"], account_type=UserAccountType.EMAIL.value
    )

    if check_password(body_dict["password"], user.password):
        return create_user_login_response(user)

    return 400, {"message": "invalid user"}


@router.get(
    "/banned/all",
    response={200: List[UserListOut]},
    auth=AuthBearer(),
    summary="차단 계정 목록 조회",
)
@paginate(PageNumberPagination, page_size=10)
def get_banned_user_list(request, query: UserListFilters = Query(...)):
    """
    차단 계정 목록 조회
    """
    is_admin(request)
    user_filters = {key: value for key, value in query.dict().items() if value}

    return (
        User.objects.annotate(
            reported_count=Count("post_reported", distinct=True)
            + Count("comment_reported", distinct=True)
        )
        .filter(status=UserStatus.BANNED.value, **user_filters)
        .order_by("-created_at")
    )


@router.post("/test/kakaotoken/", summary="카카오 소셜 로그인")
def kakao_token_test(request, token: TestKakaoToken):
    """
    클라이언트에서 카카오 소셜 로그인 후 액세스 토큰 받아서 회원가입 또는 로그인
    """
    kakao_profile = SocialLoginUserProfile(token.token, "kakao")._user_profile
    try:
        user, is_created = User.objects.get_or_create(
            social_account_id=kakao_profile["id"],
            defaults={
                "email": kakao_profile["kakao_account"].get(
                    "email", settings.KAKAO_DEFAULT_EMAIL
                ),
                "nickname": kakao_profile["kakao_account"]["profile"]["nickname"]\
                    [:NAME_AND_NICKNAME_MAX_LENGTH],
                "thumbnail_url": kakao_profile["kakao_account"]["profile"].get(
                    "thumbnail_image_url", settings.DEFAULT_USER_THUMBNAIL_URL
                ),
                "account_type": UserAccountType.KAKAO.value,
            },
        )
        return create_user_login_response(user)

    except KeyError:
        return JsonResponse({"message": "key error"}, status=400)


@router.post("/test/googletoken/", summary="구글 소셜 로그인")
def google_token_test(request, token: TestKakaoToken):
    """
    클라이언트에서 구글 소셜 로그인 후 액세스 토큰 받아서 회원가입 또는 로그인
    """
    google_profile = SocialLoginUserProfile(token.token, "google")._user_profile
    try:
        user, is_created = User.objects.get_or_create(
            social_account_id=google_profile["sub"],
            defaults={
                "email"        : google_profile["email"],
                "nickname"     : google_profile["given_name"]\
                    [:NAME_AND_NICKNAME_MAX_LENGTH],
                "thumbnail_url": google_profile["picture"],
                "account_type" : UserAccountType.GOOGLE.value,
            },
        )
        return create_user_login_response(user)

    except KeyError:
        return JsonResponse({"message": "key error"}, status=400)
