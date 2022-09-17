import socketio

sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*', logger=True)

@sio.event
def my_event(sid, message):
    print('message received with', message, sid)
    sio.emit('my_response', {'data': message})

@sio.on('send_message')
def handle_send_message_event(sid, message, nickname, room, currentTime):
    print('message', message)
    print('nickname', nickname)
    print('room', room)
    print('time', currentTime)
    data = {"user": nickname, "text": message, "time": currentTime}
    sio.emit('add_message', data, to=room)

@sio.on('join_room')
def handle_join_room_event(data):
    sio.emit('join_room_announcement', data, room=data['room'])

@sio.on('join')
def handle_join(sid, data):
    print(data)
    sio.enter_room(sid, room=data['room'])
    sio.emit('add_message', {"user": '함께하개 관리자', "text": f"{data['nickname']}님이 들어왔어요."}, to=data['room'])
    sio.emit('add_message', {"user": '함께하개 관리자', "text": f"{data['nickname']}님이 들어오셨습니다."}, to=data['room'], skip_sid=sid)

# @socketio.on('join')
# def handle_join(data):
#     print(data)
#     # app.logger.info(f"{data['nickname']}")
#     join_room(data['room'])
#     socketio.send(f"{data['nickname']}님이 들어왔어요.", to=data['room'])
#     # socketio.emit('add_message', {"user": '함께하개 관리자', "text": f"{data['nickname']}님>이 들어왔어요."})
#     socketio.emit('add_message', {"user": '함께하개 관리자', "text": f"{data['nickname']}님이 들어왔어요."}, broadcast=True)