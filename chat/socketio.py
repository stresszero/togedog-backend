import os
import socketio

from .mongodb import save_message

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")

sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*', logger=True)
users = {}

@sio.event
def connect(sid, environ, auth):
    print('connected ', sid)
    print(environ)
    print(auth)
    # auth['token']을 확인한다
    # emit 'force_disconnect'
    # 클라이언트에서 on으로 받아서 socket.disconnect()를 실행한다

@sio.on('join')
def handle_join(sid, data):
    users[sid] = data
    sio.enter_room(sid, room=data['room'])
    sio.emit(
        'add_message', 
        {"user_nickname": '함께하개 관리자', "text": f"{data['nickname']}님이 들어왔어요."}, 
        to=data['room']
    )
    # sio.emit('add_message', {"user": '함께하개 관리자', "text": f"{data['nickname']}님이 들어오셨습니다."}, to=data['room'], skip_sid=sid)

@sio.on('send_message')
def handle_send_message(sid, message, nickname, room, currentTime, userMbti, userImage, userId):
    data = {
        "user_nickname": nickname,
        "user_id"      : userId,
        "user_mbti"    : userMbti,
        "user_image"   : userImage,
        "text"         : message,
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
        {"user_nickname": '함께하개 관리자', "text": f"{leave_username}님이 퇴장하셨어요."}, 
        to=leave_room_number
    )
    del users[sid]
