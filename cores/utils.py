import logging
import jwt, requests, uuid
import boto3
from datetime import datetime, timedelta

from botocore.exceptions import ClientError

from django.http import JsonResponse
from django.conf import settings

def generate_jwt(payload, type):
    if type == "access":
        exp_days = 1
        exp = datetime.utcnow() + timedelta(days=exp_days)

    elif type == "refresh":
        exp_weeks = 2
        exp = datetime.utcnow() + timedelta(weeks=exp_weeks)

    else:
        raise Exception("invalid token type")
    
    payload['exp'] = exp
    payload['iat'] = datetime.utcnow()
    encoded_jwt    = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt

s3_client = boto3.client(
    's3',
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

image_extension_list = ["jpg", "jpeg", "jfif", "png", "webp", "avif", "svg"]

class FileUploader:
    def __init__(self, client):
        self.client = client

    def upload(self, file, type):
        try: 
            extra_args = {
                "ContentType": file.content_type,
                "ACL": "public-read"
            }

            upload_filename = f'{str(uuid.uuid4())}.{file.name.split(".")[-1]}'

            self.client.upload_fileobj(
                file,
                type,
                Key=upload_filename,
                ExtraArgs=extra_args
            )
            return f'{settings.PROFILE_IMAGES_URL}{upload_filename}' \
                if type == "user_thumbnail" else f'{settings.POST_IMAGES_URL}{upload_filename}'

        except ClientError as e:
            logging.error(e)
            return False

    def delete(self, file_name, type):
        return self.client.delete_object(Bucket=type, Key=file_name)

class FileHandler:
    def __init__(self, file_uploader):
        self.file_uploader = file_uploader
    
    def upload(self, file):
        return self.file_uploader.upload(file)
        
    def delete(self, file_name):
        return self.file_uploader.delete(file_name)


class KakaoLoginAPI:
    def __init__(self, client_id):
        self.client_id       = client_id
        self.kakao_token_uri = "https://kauth.kakao.com/oauth/token"
        self.kakao_user_uri  = "https://kapi.kakao.com/v2/user/me"
        self._access_token   = None

    def get_kakao_token(self, code):
        body = {
            "grant_type"  : "authorization_code",
            "client_id"   : self.client_id,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "code"        : code,
        }
        
        response = requests.post(self.kakao_token_uri, data=body, timeout=3)

        if not response.status_code == 200:
            return JsonResponse({'message': 'invalid response'}, status=response.status_code)

        self._access_token = response.json()["access_token"]
    # @property
    def get_kakao_profile(self):
        response = requests.post(
            self.kakao_user_uri,
            headers = {"Authorization": f"Bearer {self._access_token}"}, 
            timeout=3
        )
        
        if not response.status_code == 200:
            return JsonResponse({'message': 'invalid response'}, status=response.status_code)
        
        return response.json()

class GoogleLoginAPI:
    def __init__(self, client_id):
        self.client_id        = client_id
        self.google_token_uri = "https://oauth2.googleapis.com/token"
        self.google_user_uri  = "https://www.googleapis.com/oauth2/v3/userinfo"
        self._access_token    = None

    def get_google_token(self, code):
        body = {
            "grant_type"   : "authorization_code",
            "code"         : code,
            "client_id"    : self.client_id,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri" : settings.GOOGLE_REDIRECT_URI,
        }
        response = requests.post(self.google_token_uri, data=body, timeout=3)

        if not response.status_code == 200:
            return JsonResponse({'message': 'invalid response'}, status=response.status_code)

        self._access_token = response.json()["access_token"]
        
    def get_google_profile(self):
        response = requests.get(
            self.google_user_uri,
            headers = {"Authorization": f"Bearer {self._access_token}"}, 
            timeout=3
        )
        
        if not response.status_code == 200:
            return JsonResponse({'message': 'invalid response'}, status=response.status_code)
        
        return response.json()

class SocialLogin:
    def __init__(self, client_id):
        self.client_id       = client_id
        self.kakao_token_uri = "https://kauth.kakao.com/oauth/token"
        self.kakao_user_uri  = "https://kapi.kakao.com/v2/user/me"
        self.google_token_uri = "https://oauth2.googleapis.com/token"
        self.google_user_uri  = "https://www.googleapis.com/oauth2/v3/userinfo"
        self._access_token   = None
    
    def get_token(self, code, type):
        if type == "kakao":
            body = {
                "grant_type"  : "authorization_code",
                "client_id"   : self.client_id,
                "redirect_uri": settings.KAKAO_REDIRECT_URI,
                "code"        : code,
            }
            response = requests.post(self.kakao_token_uri, data=body, timeout=3)

        elif type == "google":
            body = {
                "grant_type"   : "authorization_code",
                "code"         : code,
                "client_id"    : self.client_id,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri" : settings.GOOGLE_REDIRECT_URI,
            }
            response = requests.post(self.google_token_uri, data=body, timeout=3)

        else:
            raise Exception("invalid type")

        if not response.status_code == 200:
            return JsonResponse({'message': 'invalid response'}, status=response.status_code)

        self._access_token = response.json()["access_token"]
    
    def get_profile(self, type):
        if type == "kakao":
            response = requests.post(
                self.kakao_user_uri,
                headers = {"Authorization": f"Bearer {self._access_token}"}, 
                timeout=3
            )

        elif type == "google":
            response = requests.get(
                self.google_user_uri,
                headers = {"Authorization": f"Bearer {self._access_token}"}, 
                timeout=3
            )

        else:
            raise Exception("invalid type")

        if not response.status_code == 200:
            return JsonResponse({'message': 'invalid response'}, status=response.status_code)
        
        return response.json()

