import logging
import jwt, requests, uuid
import boto3
from datetime import datetime, timedelta

from botocore.exceptions import ClientError

from django.http import JsonResponse
from django.conf import settings
from ninja.errors import HttpError
from ninja.files import UploadedFile


MB = 1024 * 1024
IMAGE_EXTENSIONS_LIST = ["jpg", "jpeg", "jfif", "png", "webp", "avif", "svg"]


def generate_jwt(payload, type):
    if type == "access":
        exp = datetime.utcnow() + timedelta(days=1)

    elif type == "refresh":
        exp = datetime.utcnow() + timedelta(weeks=2)

    else:
        raise Exception("invalid token type")

    payload["exp"] = exp
    payload["iat"] = datetime.utcnow()
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


s3_client = boto3.client(
    "s3",
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)


def validate_upload_file(file: UploadedFile) -> bool:
    if not file:
        return False
    if file.name.split(".")[-1].lower() not in IMAGE_EXTENSIONS_LIST:
        raise HttpError(400, "invalid file extension")
    if file.size > 50 * MB:
        raise HttpError(400, "file size is too large")
    return True


def handle_upload_file(file: UploadedFile, type: str) -> str:
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
    욕설이 포함된 경우 해당 단어를 *로 치환
    """
    censored = False
    censored_text = text
    censored = True
    for bad_word in settings.BAD_WORDS_LIST:
        bad_word_length = len(bad_word)
        bad_word_index = text.find(bad_word)

        while bad_word_index != -1:
            censored_text = (
                censored_text[:bad_word_index] + "*" * bad_word_length
            ) + censored_text[bad_word_index + bad_word_length :]

            bad_word_index = text.find(bad_word, bad_word_index + 1)
    return censored_text


# google oauth class, get google auth code by client
class GoogleOAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_access_token(self, code):
        url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        response = requests.post(url, data=data)
        return response.json()

    def get_user_info(self, access_token):
        url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        return response.json()
