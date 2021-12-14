import os
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sched.settings")
django_asgi_app = get_asgi_application()
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import note.task.routing
from sched.token_auth import TokenAuthMiddleware
application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(
            note.task.routing.websocket_urlpatterns
        )
    ),
})