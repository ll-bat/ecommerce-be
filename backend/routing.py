from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from base.middleware import JwtTokenAuthMiddleware
from chat import urls

application = ProtocolTypeRouter({
    "websocket": JwtTokenAuthMiddleware(
        URLRouter(
            urls.websocket_urlpatterns
        )
    ),
})
