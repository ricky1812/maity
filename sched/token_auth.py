from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs
from django.urls import resolve
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.backends import TokenBackend
from user.models import User


@database_sync_to_async
def get_user(scope):
    try:
        #print(scope)
        token_key = parse_qs(scope["query_string"].decode("utf8"))["token"][0]
        #print("!!!!   ",token_key)

        try:
            valid_data = TokenBackend(algorithm='HS256').decode(token_key, verify=False)
            print(valid_data)
            user_id = valid_data['user_id']
            user=User.objects.get(id=user_id)
            print("~~~~~~~~~~~~",user)
            return user
        except ValidationError as v:
            print("validation error", v)
    except Exception as e:
        print(e)


class TokenAuthMiddleware:

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return TokenAuthMiddlewareInstance(scope, self)


class TokenAuthMiddlewareInstance:
    def __init__(self, scope, middleware):

        self.scope = dict(scope)
        self.inner = middleware.inner

    async def __call__(self, receive, send):
        self.scope['user'] = await get_user(self.scope)
        inner = self.inner(self.scope)
        return await inner(receive, send)


TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))