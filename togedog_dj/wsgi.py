import os
import socketio
import eventlet
import eventlet.wsgi

from django.core.wsgi import get_wsgi_application

from chat.socketio import sio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")

# django wsgi app
application = get_wsgi_application()

# create a Socket.IO server with eventlet
# sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*')

application = socketio.WSGIApp(sio, application)

# eventlet.wsgi.server(eventlet.listen(("", 8000)), application)

