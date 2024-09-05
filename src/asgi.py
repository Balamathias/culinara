"""
ASGI config for src project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from typing import Any

from django.core.asgi import get_asgi_application
from django.core.handlers.asgi import ASGIHandler
from channels.routing import ProtocolTypeRouter, URLRouter

from api.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')

application: ASGIHandler = get_asgi_application()

application: Any = ProtocolTypeRouter({
  'http': application,
  'websocket': URLRouter(websocket_urlpatterns),
})
