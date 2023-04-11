from . import views
from django.urls import path

urlpatterns = [
    path("login/", views.login_view, name="api-login-view"),    
    path("autologin/", views.login_with_zerodha,name="API-Autologin"),
    path("algowatch", views.algowatch,name="API-Algowatch"),
    path("manualwatch",  views.manualwatch, name="API-Manualwatch"),
    path("orders",  views.OrdersApi, name="API-Orders"),
    path('positions/', views.PositionsApi,name="positionsapi"),
    path("settings",  views.settings_view, name="API-Settings"), 
    path('startAlgo/', views.StartAlgoAPI.as_view(), name='StartAlgoAPI'),
    path('stopAlgo/', views.StopAlgoAPI.as_view(), name='StopAlgoAPI'),
    path('startAll/', views.StartAllAPI.as_view(), name='StartAllAPI'),
    path('buySingle/', views.BuySingleAPI.as_view(), name='BuySingleAPI'),
    path('sellSingle/', views.SellSingle.as_view(), name='SellSingle'),
    path('scaleUpQty/', views.ScaleUpQtyAPI.as_view(), name='ScaleUpQtyAPI'),
    path('scaleDownQty/', views.ScaleDownQtyAPI.as_view(), name='ScaleDownQtyAPI'),
    path('addInstrument/', views.AddInstrumentAPI.as_view(), name='AddInstrumentAPI'),
    path('deleteInstrument/', views.DeleteInstrumentAPI.as_view(), name='DeleteInstrumentAPI'),    
]