from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from base.middleware import AuthTokenAuthMiddleware
from chat import urls

application = ProtocolTypeRouter({
    "websocket": AuthTokenAuthMiddleware(
        URLRouter(
            urls.websocket_urlpatterns
        )
    ),
})
