from django.urls import path
from .consumers import *

websocket_urlpatterns = [
    # path('ws/stock/<str:token>',MyAsyncConsumer.as_asgi()),
    path('ws/stock/',MyAsyncConsumer.as_asgi()),
]