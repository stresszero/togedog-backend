import socketio
from bson import ObjectId
from pymongo import MongoClient, DESCENDING

from django.conf import settings

sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*', logger=True)

client = MongoClient(settings.MONGODB_ADDRESS)

chat_db = client.get_database("mbtichat")
messages_collection = chat_db.get_collection("messages")
# users_collection = chat_db.get_collection("users")
# rooms_collection = chat_db.get_collection("rooms")
# room_members_collection = chat_db.get_collection("room_members")

users = {}

@sio.event
def my_event(sid, message):
    print('message received with', message, sid)
    sio.emit('my_response', {'data': message})

@sio.on('join')
def handle_join(sid, data):
    users[sid] = data
    sio.enter_room(sid, room=data['room'])
    sio.emit('add_message', {"user": '함께하개 관리자', "text": f"{data['nickname']}님이 들어왔어요."}, to=data['room'])
    # sio.emit('add_message', {"user": '함께하개 관리자', "text": f"{data['nickname']}님이 들어오셨습니다."}, to=data['room'], skip_sid=sid)

@sio.on('send_message')
def handle_send_message(sid, message, nickname, room, currentTime, userMbti):
    print(message, nickname, room, currentTime, userMbti)
    data = {"user": nickname, "text": message, "time": currentTime, "mbti": userMbti}
    sio.emit('add_message', data, to=room)

@sio.event
def disconnect(sid):
    leave_username = users.get(sid).get('nickname')
    leave_room_number = users.get(sid).get('room')
    sio.emit('add_message', {"user": '함께하개 관리자', "text": f"{leave_username}님이 퇴장하셨어요."}, to=leave_room_number)
    del users[sid]
