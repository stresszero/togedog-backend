import os
import socketio

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")
django.setup()

from .mongodb import save_message
from cores.models import UserStatus
from cores.utils import censor_text
from users.models import User

sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*', logger=True)

users = {}

@sio.event
def connect(sid, environ, auth):
    '''
    socket.io 클라이언트가 연결되면 아래 코드 실행
    auth의 사용자id값으로 해당 사용자가 존재하지않거나 차단유저이면 connect_error로 emit
    emit 되면 클라이언트 쪽에서 강제로 연결해제 처리
    '''
    user = User.objects.filter(id=auth["userId"]) 
    if not user.exists() or user.get().status == UserStatus.BANNED.value:
        sio.emit('connect_error', {'message': 'invalid user'})

@sio.on('join')
def handle_join(sid, data):
    '''
    유저가 채팅방에 입장하면 아래 코드 실행
    브라우저에서 채팅방 입장시 connect 이벤트가 먼저 발생하고 이어서 join 이벤트가 발생됨
    data를 자바스크립트 객체로 받으면 파이썬 딕셔너리로 사용 가능
    data에는 방 번호와 사용자 닉네임이 포함됨
    채팅방에 접속한 사용자의 sid값을 key로 하고, data를 value로 users 딕셔너리에 저장    
    '''
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
    '''
    send_message 이벤트로 받은 데이터를 욕설 필터링과 MongoDB에 저장하고 add_message로 emit
    censor_text(): 욕설 필터링 함수, 욕설 부분이 있으면 *으로 수정한 문자열을 반환함
    save_message(): MongoDB에 메시지 데이터를 저장하고 고유한 ObjectId(24자리 문자열)반환
    필요한 데이터 처리가 완료되면 데이터를 add_message로 emit
    '''
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
    '''
    socket.io 클라이언트가 연결 해제되면 아래 코드 실행
    leave_username: 연결 해제된 sid값의 유저 닉네임
    leave_room_number: 연결 해제된 sid값의 방 번호
    퇴장한 사용자 정보를 담아 add_message로 emit
    users 딕셔너리에서 해당 sid값의 데이터 삭제
    '''
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
