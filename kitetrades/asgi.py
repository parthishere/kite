import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import playground.routing
# from channels.auth import AuthMiddlewareStack
# from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitetrades.settings')
django.setup()

django_asgi_app = get_asgi_application()

# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     'websocket': AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(
#             playground.routing.websocket_urlpatterns
#         )))
# })

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    'websocket': URLRouter(
            playground.routing.websocket_urlpatterns
        )
})