import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterator

import boto3
import botocore
import jwt
import requests
from django.conf import settings
from django.http import JsonResponse
from django.urls import URLPattern
from django.urls import path as django_path
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja.router import Router
from ninja.utils import normalize_path, replace_path_param_notation

from users.models import User

MB = 1024 * 1024
IMAGE_EXTENSIONS_LIST = ["jpg", "jpeg", "jfif", "png", "webp", "avif", "svg"]

EXP_DAYS = 1
EXP_WEEKS = 2
COOKIE_MAX_AGE_HOUR = 8


# https://github.com/vitalik/django-ninja/issues/575
class URLBugFixedRouter(Router):
    def urls_paths(self, prefix: str) -> Iterator[URLPattern]:
        prefix = replace_path_param_notation(prefix)
        for path, path_view in self.path_operations.items():
            path = replace_path_param_notation(path)
            route = "/".join([i for i in (prefix, path) if i])
            # to skip lot of checks we simply treat double slash as a mistake:
            route = normalize_path(route)
            route = route.lstrip("/")

            for operation in path_view.operations:
                url_name = self.api.get_operation_url_name(operation, router=self)
                yield django_path(route, path_view.get_view(), name=url_name)


class FileHandler:
    def __init__(self, file_service):
        self.file_service = file_service

    def upload(self, file, type, upload_filename, extra_args):
        return self.file_service.upload(file, type, upload_filename, extra_args)

    def delete(self, type, url):
        return self.file_service.delete(type, url)


class S3Service:
    def __init__(self):
        self.endpoint_url = settings.AWS_S3_ENDPOINT_URL
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        self.region_name = settings.AWS_S3_REGION_NAME

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region_name,
        )

    def upload(self, file, type, upload_filename, extra_args):
        try:
            self.s3_client.upload_fileobj(
                Fileobj=file,
                Bucket=type,
                Key=upload_filename,
                ExtraArgs=extra_args,
            )
        except botocore.exceptions.ClientError as error:
            raise HttpError(400, "S3 service is not available") from error

    def delete(self, type, url):
        try:
            self.s3_client.delete_object(Bucket=type, Key=url.split("/")[-1])

        except botocore.exceptions.ClientError as error:
            raise HttpError(400, "S3 service is not available") from error


s3_service = S3Service()
file_handler = FileHandler(s3_service)


def validate_upload_file(file: UploadedFile):
    if not file:
        return False

    if file.name.split(".")[-1].lower() not in IMAGE_EXTENSIONS_LIST:
        raise HttpError(400, "invalid file extension")

    if file.size > 50 * MB:
        raise HttpError(400, "file size is too large")

    return True


def delete_existing_image(url: str, type: str):
    if type not in ["user_thumbnail", "post_images"]:
        raise HttpError(400, "invalid type")

    if (
        type == "user_thumbnail"
        and url != settings.DEFAULT_USER_THUMBNAIL_URL
        and url.startswith(settings.PROFILE_IMAGES_URL)
    ):
        file_handler.delete(type, url)

    if type == "post_images" and url != settings.DEFAULT_POST_IMAGE_URL:
        file_handler.delete(type, url)


def handle_upload_file(file: UploadedFile, type: str):
    if type not in ["user_thumbnail", "post_images"]:
        raise HttpError(400, "invalid type")

    upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'
    url_dict = {
        "user_thumbnail": f"{settings.PROFILE_IMAGES_URL}{upload_filename}",
        "post_images": f"{settings.POST_IMAGES_URL}{upload_filename}",
    }

    file_handler.upload(
        file,
        type,
        upload_filename,
        extra_args={"ACL": "public-read", "ContentType": file.content_type},
    )
    return url_dict[type]


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
    def __init__(self, access_token, type: str):
        self.kakao_profile_uri = settings.KAKAO_PROFILE_URI
        self.google_profile_uri = settings.GOOGLE_PROFILE_URI
        self._user_profile = None

        if type == "kakao":
            self.get_kakao_profile(access_token)
        elif type == "google":
            self.get_google_profile(access_token)
        else:
            raise ValueError("invalid social login type")

    def get_kakao_profile(self, access_token: str):
        response = requests.post(
            self.kakao_profile_uri,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=3,
        )
        if response.status_code != 200:
            raise HttpError(400, "invalid kakao access token")
        self._user_profile = response.json()

    def get_google_profile(self, access_token: str):
        response = requests.post(
            self.google_profile_uri,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=3,
        )
        if response.status_code != 200:
            raise HttpError(400, "invalid google access token")
        self._user_profile = response.json()


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
