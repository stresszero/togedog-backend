import asyncio
import socketio

# create a Socket.IO server
sio = socketio.Server()

# wrap with a WSGI application
app_wsgi = socketio.WSGIApp(sio)

# create a Socket.IO async server
sio_async = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# wrap with ASGI application
app_asgi = socketio.ASGIApp(sio)

# sio.event test
@sio_async.event
async def my_event(sid, message):
    print('message received with ', message, sid)
    # await sio_async.emit('receive_message', message, room=sid)
    await sio_async.emit('my_response', {'data': message['data']}, room=sid)
