import jwt, requests
import boto3
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.conf import settings

def generate_jwt(payload, type):
    if type == "access":
        exp_days = 1
        exp = datetime.utcnow() + timedelta(days=exp_days)

    if type == "refresh":
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