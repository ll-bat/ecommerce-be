import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from base.middleware import AuthTokenAuthMiddleware
from chat import urls

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthTokenAuthMiddleware(
        URLRouter(urls.websocket_urlpatterns)
    ),
})
