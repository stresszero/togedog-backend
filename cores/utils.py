import jwt, requests, uuid
import boto3
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.http import JsonResponse
from ninja.errors import HttpError
from ninja.files import UploadedFile

from users.models import NAME_AND_NICKNAME_MAX_LENGTH, User

MB = 1024 * 1024
IMAGE_EXTENSIONS_LIST = ["jpg", "jpeg", "jfif", "png", "webp", "avif", "svg"]

EXP_DAYS = 1
EXP_WEEKS = 2
COOKIE_MAX_AGE_HOUR = 8


def generate_jwt(payload: dict, type: str):
    if type == "access":
        exp = datetime.now(timezone.utc) + timedelta(days=EXP_DAYS)

    elif type == "refresh":
        exp = datetime.now(timezone.utc) + timedelta(weeks=EXP_WEEKS)

    else:
        raise ValueError("invalid token type")

    payload["exp"] = exp
    payload["iat"] = datetime.now(timezone.utc)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


s3_client = boto3.client(
    "s3",
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)


def validate_upload_file(file: UploadedFile):
    if not file:
        return False
    if file.name.split(".")[-1].lower() not in IMAGE_EXTENSIONS_LIST:
        raise HttpError(400, "invalid file extension")
    if file.size > 50 * MB:
        raise HttpError(400, "file size is too large")
    return True


def delete_existing_image(url: str, type: str):
    if (
        type == "user_thumbnail"
        and url != settings.DEFAULT_USER_THUMBNAIL_URL
        and url.startswith(settings.PROFILE_IMAGES_URL)
    ):
        s3_client.delete_object(Bucket="user_thumbnail", Key=url.split("/")[-1])

    if type == "post_image" and url != settings.DEFAULT_POST_IMAGE_URL:
        s3_client.delete_object(Bucket="post_images", Key=url.split("/")[-1])


def handle_upload_file(file: UploadedFile, type: str):
    upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
    if type == "user_thumbnail":
        url = f"{settings.PROFILE_IMAGES_URL}{upload_filename}"
    elif type == "post_images":
        url = f"{settings.POST_IMAGES_URL}{upload_filename}"
    else:
        raise HttpError(400, "invalid upload type")
    s3_client.upload_fileobj(
        file,
        type,
        upload_filename,
        ExtraArgs={"ACL": "public-read", "ContentType": file.content_type},
    )
    return url


def censor_text(text: str) -> str:
    """
    욕설 목록에 있는 모든 욕설을 text에 있는지 확인하기 위해 text.find()로 검색
    욕설이 포함된 경우 그 부분만 *로 바꿈
    """
    censored_text = text
    for bad_word in settings.BAD_WORDS_LIST:
        bad_word_length = len(bad_word)
        bad_word_index = text.find(bad_word)

        while bad_word_index != -1:
            censored_text = (
                censored_text[:bad_word_index]
                + "*" * bad_word_length
                + censored_text[bad_word_index + bad_word_length :]
            )
            bad_word_index = text.find(bad_word, bad_word_index + 1)
    return censored_text


class SocialLoginUserProfile:
    def __init__(self, code, type: str):
        self.kakao_profile_uri = settings.KAKAO_PROFILE_URI
        self.google_profile_uri = settings.GOOGLE_PROFILE_URI
        self._user_profile = None

        if type == "kakao":
            self.get_kakao_profile(code)
        elif type == "google":
            self.get_google_profile(code)
        else:
            raise ValueError("invalid social login type")

    def get_kakao_profile(self, code: str):
        response = requests.post(
            self.kakao_profile_uri,
            headers={"Authorization": f"Bearer {code}"},
            timeout=3,
        )
        if response.status_code != 200:
            raise HttpError(400, "invalid kakao access token")
        self._user_profile = response.json()

    def get_google_profile(self, code: str):
        response = requests.get(
            self.google_profile_uri,
            headers={"Authorization": f"Bearer {code}"},
            timeout=3,
        )
        if response.status_code != 200:
            raise HttpError(400, "invalid google access token")
        self._user_profile = response.json()


def create_user_login_response(
    user: User,
    httponly: bool = True,
    samesite: str = "Lax",
    secure: bool = True,
    max_age: timedelta = timedelta(hours=COOKIE_MAX_AGE_HOUR),
) -> JsonResponse:
    data = {
        "access_token": generate_jwt({"user": user.id}, "access"),
        "user": user.get_user_info_dict,
    }
    response = JsonResponse(data, status=200)
    response.set_cookie(
        "access_token",
        data["access_token"],
        httponly=httponly,
        samesite=samesite,
        secure=secure,
        max_age=max_age,
    )
    response.set_cookie(
        "refresh_token",
        generate_jwt({"user": user.id}, "refresh"),
        httponly=httponly,
        samesite=samesite,
        secure=secure,
        max_age=max_age,
    )
    return response