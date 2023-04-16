from . import views
from django.urls import path

urlpatterns = [
    path("login/", views.login_view, name="api-login-view"),    
    path("login-check/", views.login_check_view, name="api-login-view"),    
    path("autologin/", views.login_with_zerodha,name="API-Autologin"),
    path("algowatch", views.algowatch,name="API-Algowatch"),
    path("manualwatch",  views.manualwatch, name="API-Manualwatch"),
    path("orders",  views.OrdersApi, name="API-Orders"),
    path('positions/', views.PositionsModelApi,name="positionsapi"),
    # path('live-positions/', views.getPositions,name="positionsapi-live"),
    path("settings/<int:pk>",  views.SettingsView.as_view   (), name="API-Settings"), 
    path('startAlgo/', views.StartAlgoSingleAPI.as_view(), name='StartAlgoSingleAPI'),
    path('stopAlgo/', views.StopAlgoAndManualSingleAPI.as_view(), name='StopAlgoSingleAPI'),
    path('startAll/', views.StartAllAPI.as_view(), name='StartAllAPI'),
    path('buySingle/', views.BuySingleManualAPI.as_view(), name='BuySingleManualAPI'),
    path('sellSingle/', views.SellSingle.as_view(), name='SellSingle'),
    path('scaleUpQty/', views.ScaleUpQtyAPI.as_view(), name='ScaleUpQtyAPI'),
    path('scaleDownQty/', views.ScaleDownQtyAPI.as_view(), name='ScaleDownQtyAPI'),
    path('addInstrument/', views.AddInstrumentAPI.as_view(), name='AddInstrumentAPI'),
    path('deleteInstrument/', views.DeleteInstrumentAPI.as_view(), name='DeleteInstrumentAPI'),  
    path("logout", views.logoutUser, name="API-Logout"),  
    
    # search
]