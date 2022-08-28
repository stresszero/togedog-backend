import jwt
from datetime import datetime, timedelta

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