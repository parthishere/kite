from django.urls import path
from . import views

#URLConf
urlpatterns = [
    path("", views.index, name="Home"),
    path("login", views.loginUser,name="Login"),
    path("algowatch", views.algowatch,name="Algowatch"),
    path("manualwatch", views.manualwatch, name="Manualwatch"),
    path("settings", views.settings, name="Settings"),
    path("logout", views.logoutUser, name="Logout"),
]