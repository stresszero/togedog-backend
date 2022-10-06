# from django.contrib import admin
from django.urls import path, include

from api import api

urlpatterns = [
    path("", api.urls),
    # path('debug-toolbar/', include('debug_toolbar.urls')),
]
