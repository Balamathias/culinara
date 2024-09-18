from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
    # re_path(r'ws/post/$', consumers.PostConsumer.as_asgi()),
    # re_path(r'^ws/users/$', consumers.UserConsumer.as_asgi()),
]
