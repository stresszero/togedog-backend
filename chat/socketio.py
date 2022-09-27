import os
import socketio

import django
from .mongodb import save_message
from django.conf import settings

from cores.utils import censor_text

django.setup()

from users.models import User

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")

sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*', logger=True)
users = {}

@sio.event
def connect(sid, environ, auth):
    print('connected ', sid)
    print(auth)
    if User.objects.get(id=auth['userId']).status == "banned":
        sio.emit('connect_error', {'message': 'invalid user'})
    # auth['token']을 확인하고 유효하지 않은 JWT를 보낸 경우
    # 차단유저가 들어온 경우
    # emit 'connect_error' 으로 전송한다
    # 클라이언트에서 on으로 받아서 socket.disconnect() 또는 close()를 실행한다
    # 클라이언트에서 모달창을 띄워주고 홈으로 리다이렉트 시킨다

# @sio.on('connect_error')
# def handle_connect_error(sid, data):
#     sio.disconnect()

@sio.on('join')
def handle_join(sid, data):
    users[sid] = data
    sio.enter_room(sid, room=data['room'])
    sio.emit(
        'add_message', 
        {
            "user_nickname": '함께하개 관리자', 
            "text": f"{data['nickname']}님이 들어왔어요."
        }, 
        to=data['room']
    )

@sio.on('send_message')
def handle_send_message(sid, message, nickname, room, currentTime, userMbti, userImage, userId):
    data = {
        "user_nickname": nickname,
        "user_id"      : userId,
        "user_mbti"    : userMbti,
        "user_image"   : userImage,
        "text"         : censor_text(message),
        "message_id"   : save_message(message, nickname, userId, room),
        "time"         : currentTime,
    }
    sio.emit('add_message', data, to=room)

@sio.event
def disconnect(sid):
    leave_username = users[sid].get('nickname')
    leave_room_number = users[sid].get('room')
    sio.emit(
        'add_message', 
        {
            "user_nickname": '함께하개 관리자', 
            "text": f"{leave_username}님이 퇴장하셨어요."
        }, 
        to=leave_room_number
    )
    del users[sid]
