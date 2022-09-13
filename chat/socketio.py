import asyncio
import socketio
import json
import eventlet

from togedog_dj.wsgi import sio
# create a Socket.IO server
# sio = socketio.Server()

# sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*')
# sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*', cors_credentials=True)

# wrap with a WSGI application
# app_wsgi = socketio.WSGIApp(sio)

# create a Socket.IO async server
# sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# wrap with ASGI application
# app_asgi = socketio.ASGIApp(sio)



# sio.event test
@sio.event
def my_event(sid, message):
    print('message received with', message, sid)
    # await sio.emit('receive_message', message, room=sid)
    # await sio.emit('my_response', {'data': message}, room=sid)
    sio.emit('my_response', {'data': message['data']}, room=sid)

@sio.on('connection')
def connection(sid, data):
    print('socketio client connected')

@sio.on('입장')
def entrance(sid, data):
    print(data)
    print('입장', data['nickname'])
    sio.enter_room(sid, data['room'])
    print("entered room")
    sio.emit('add_message', "ASDF", room=data['room'])
    print("emitted 1")
    # sio.emit('add_message', json.dumps({'user': '함께하개 관리자', 'text': '님의 입장을 환영합니다!'}), skip_sid=sid)

@sio.event
def send_message(sid, data):
    print(data)
    # print('send_message', message, nickname, room, time)
    # await sio.emit('add_message', {'user': nickname, 'text': message, 'time': time}, room)
    # await sio.emit('add_message', 'test', room)
    print('emitted')

@sio.event
def disconnect(sid, data):
    print('disconnect')
    sio.emit('add_message', {'user': '함께하개 관리자', 'text':  '님이 나가셨습니다.'}, skip_sid=sid)
