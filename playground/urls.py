from django.urls import path
from . import views

#URLConf
urlpatterns = [
    path("", views.homelogin, name="Home"),
    path("algowatch", views.algowatch,name="Algowatch"),
    path("manualwatch", views.manualwatch, name="Manualwatch"),
    path("settings", views.settings, name="Settings"),
]