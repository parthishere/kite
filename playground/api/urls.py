from .views import *
from django.urls import path

urlpatterns = [
    path("login/", login_view, name="api-login-view"),

    # path("algowatch",  algowatch,name="Algowatch"),
    # path("manualwatch",  manualwatch, name="Manualwatch"),
    # path("orders",  orders, name="Orders"),
    # path("settings",  api_settings, name="Settings"),
    # path("logout",  logoutUser, name="Logout"),

    # #Ajax function to call from script to view
    # path("startAlgo",  startSingle),
    # path("stopAlgo",  stopSingle),
    # path("startAll",  startAll),
    # path("stopAll",  stopAll),
    # path("buySingle",  buySingle),
    # path("sellSingle",  sellSingle),

    # path("scaleUpQty",  scaleUpQty),
    # path("scaleDownQty",  scaleDownQty),

    # path("addInstrument",  addInstrument),
    # path("deleteInstrument",  deleteInstrument),
]