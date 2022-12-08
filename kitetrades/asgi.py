import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitetrades.settings')
import django
django.setup()


from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()


from channels.routing import ProtocolTypeRouter, URLRouter
import playground.routing
# from channels.auth import AuthMiddlewareStack
# from channels.security.websocket import AllowedHostsOriginValidator



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

