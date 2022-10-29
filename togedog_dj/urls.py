from django.urls import path

from api import api

urlpatterns = [
    path("api/", api.urls),
    # path('debug-toolbar/', include('debug_toolbar.urls')),
]
