from .views import *
from django.urls import path

urlpatterns = [
    path("login/", login_view, name="api-login-view"),
]