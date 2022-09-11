import os

from django.core.asgi import get_asgi_application
import socketio
from .socketio import sio_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")

django_app = get_asgi_application()
application = socketio.ASGIApp(sio_async, django_app)

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     # Just HTTP for now. (We can add other protocols later.)
# })

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
# django_asgi_app = get_asgi_application()

# application = ProtocolTypeRouter({
#   "http": django_asgi_app,
#   "websocket": AllowedHostsOriginValidator(
#         AuthMiddlewareStack(
#             URLRouter(
#                 chat.routing.websocket_urlpatterns
#             )
#         )
#     ),
# })

