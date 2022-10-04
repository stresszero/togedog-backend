import os
import socketio

from django.core.wsgi import get_wsgi_application

from chat.socketio import sio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")

# django wsgi app
application = get_wsgi_application()

# wrap with socketio's middleware
application = socketio.WSGIApp(sio, application)

# eventlet를 직접 실행하는 코드, gunicorn with eventlet 사용시 주석처리 할 것
# eventlet.wsgi.server(eventlet.listen(("", 8000)), application)
