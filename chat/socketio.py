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

@sio.on('join')
def handle_join(sid, data):
    users[sid] = data
    sio.enter_room(sid, room=data['room'])
    sio.emit(
        'add_message', 
        {"user": '함께하개 관리자', "text": f"{data['nickname']}님이 들어왔어요."}, 
        to=data['room']
    )
    # sio.emit('add_message', {"user": '함께하개 관리자', "text": f"{data['nickname']}님이 들어오셨습니다."}, to=data['room'], skip_sid=sid)

@sio.on('send_message')
def handle_send_message(sid, message, nickname, room, currentTime, userMbti):
    data = {
        "user"      : nickname,
        # "user_id"   : user_id,
        "text"      : message,
        "time"      : currentTime,
        "mbti"      : userMbti,
        "message_id": save_message(message, nickname, room),
        # "message_id": save_message(message, user_id, room),
    }
    # data['message_id'] = save_message(room, data['text'], data['user'])
    sio.emit('add_message', data, to=room)

@sio.event
def disconnect(sid):
    leave_username = users[sid].get('nickname')
    leave_room_number = users[sid].get('room')
    sio.emit(
        'add_message', 
        {"user": '함께하개 관리자', "text": f"{leave_username}님이 퇴장하셨어요."}, 
        to=leave_room_number
    )
    del users[sid]
