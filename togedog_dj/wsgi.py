import os
import socketio
import eventlet
import eventlet.wsgi

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")

django_app = get_wsgi_application()

sio = socketio.Server(async_mode='eventlet', cors_allowed_origins='*', cors_credentials=True)

application = socketio.WSGIApp(sio, django_app)

eventlet.wsgi.server(eventlet.listen(("", 8000)), application)


