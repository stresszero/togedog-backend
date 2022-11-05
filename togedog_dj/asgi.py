import os

import socketio
from django.core.asgi import get_asgi_application

# from chat.socketio import sio_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")

django_app = get_asgi_application()
# application = socketio.ASGIApp(sio_async, django_app)
