"""
ASGI config for foodgram project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from api import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/echo/", consumers.EchoConsumer.as_asgi()),
            path("ws/notify/", consumers.NotifyConsumer.as_asgi()),
        ])
    ),
})
