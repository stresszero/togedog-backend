import socketio
from django.core.wsgi import get_wsgi_application

from chat.socketio import sio

# django wsgi app
application = get_wsgi_application()

# wrap with socketio's middleware
application = socketio.WSGIApp(sio, application)
