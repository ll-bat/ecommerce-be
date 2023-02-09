from urllib.parse import parse_qs

from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework_simplejwt.authentication import JWTAuthentication

from base.models import User


class JwtTokenAuthMiddleware:
    """
    JWT token authorization middleware for Django Channels 2
    Assumes Websocket urls in the format:
      ws://domain.com/ws/objects/5?access_token=your_access_token_here_ABCDEFT123456
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            queries = parse_qs(scope['query_string'].strip().decode())
            raw_token = queries['access_token'][0]
            auth = JWTAuthentication()
            validated_token = auth.get_validated_token(raw_token)
            user = await sync_to_async(auth.get_user)(validated_token)
            scope['user'] = user
        except Exception as e:
            print(e)
            scope['user'] = AnonymousUser()
        return await self.inner(dict(scope), receive, send)


class AuthTokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            queries = parse_qs(scope['query_string'].strip().decode())
            raw_token = queries['access_token'][0]
            query = User.objects.filter(auth_token__key=raw_token)
            user = await sync_to_async(query.first)()
            scope['user'] = user
        except Exception as e:
            print(e)
            scope['user'] = AnonymousUser()
        return await self.inner(dict(scope), receive, send)
