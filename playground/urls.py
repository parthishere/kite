from django.urls import path
from . import views

#URLConf
urlpatterns = [
    path("", views.index, name="HomeIndex"),
    path("login", views.loginUser,name="Login"),
    path("autologin", views.loginWithZerodha,name="Autologin"),
    path("home", views.home,name="Home"),
    path("algowatch", views.algowatch,name="Algowatch"),
    path("manualwatch", views.manualwatch, name="Manualwatch"),
    path("orders", views.orders, name="Orders"),
    path("settings", views.settings, name="Settings"),
    path("logout", views.logoutUser, name="Logout"),

    #Ajax function to call from script to view
    path("startAlgo", views.startSingle),
    path("stopAlgo", views.stopSingle),
    path("startAll", views.startAll),
    path("stopAll", views.stopAll),
    path("buySingle", views.buySingle),
    path("sellSingle", views.sellSingle),

    path("scaleUpQty", views.scaleUpQty),
    path("scaleDownQty", views.scaleDownQty),

    path("addInstrument", views.addInstrument),
    path("deleteInstrument", views.deleteInstrument),
]