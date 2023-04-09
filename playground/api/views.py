from rest_framework.decorators import api_view
from rest_framework.response import Response    
from django.shortcuts import render, redirect
from kiteconnect import KiteConnect
from django.conf import settings
import threading
from ..views import coreLogic,login_in_zerodha,getPositions, total_pnl
import pyotp
from ..models import AlgoWatchlist,Instruments, ManualWatchlist, Orders, Preferences
from .serializers import AlgoWatchlistSerializer, PreferencesSerializer, InstrumentsSerializer,OrderSerializer
from datetime import datetime

kite = KiteConnect(api_key=settings.KITE_API_KEY)

coreLogicLock = threading.Lock()
coreRunning = False

kite = KiteConnect(api_key=settings.KITE_API_KEY)

@api_view(["GET"])
def login_view(request):    
    if 'request_token' in request.GET and request.GET.get('request_token'):
        try:
            data = kite.generate_session(
                request.GET['request_token'], api_secret=settings.KITE_API_SECRET)
            kite.set_access_token(data["access_token"])
        except Exception as e:
            return Response({"Error": f"Something wrong happed, Error {e}"})
        coreLogic()
        return Response({'Data':"Login Successful"})   
    else:
        return Response({"Error": "No request token found in callback url"}) 

@api_view(['GET'])
def login_with_zerodha(request):            
    topt = pyotp.TOTP('ZF3MONJ23XF34ESGSGRXOKR6RGTRQLXN')
    toptKey = topt.now()        
    kite = login_in_zerodha(settings.KITE_API_KEY, settings.KITE_API_SECRET, 'LN7447', 'zzzzaaaa', toptKey)
    profile = kite.profile()
    print(profile)
    return Response({"Status":"success"})


@api_view(["GET"])
def algowatch(request):
        
    if kite.access_token is None:
        return redirect("/")
    positionArray = getPositions()
    totalPNL = total_pnl() or 0
    algoWatchlistArray = AlgoWatchlist.objects.all()
    allInstruments = list(Instruments.objects.all(
    ).values_list('tradingsymbol', flat=True))
    return Response({'allInstruments': allInstruments, 'algoWatchlistArray': algoWatchlistArray, 'positionArray': positionArray, 'totalPNL': totalPNL})

@api_view(["GET"])
def manualwatch(request):
    if kite.access_token is None:
        return redirect("/")
    positionArray = getPositions()
    totalPNL = total_pnl()
    manualWatchlistArray = ManualWatchlist.objects.all()
    allInstruments = list(Instruments.objects.all(
    ).values_list('tradingsymbol', flat=True))
    return Response({'allInstruments': allInstruments, 'manualWatchlistArray': manualWatchlistArray, 'positionArray': positionArray, 'totalPNL': totalPNL})


@api_view(['GET'])
def OrdersApi(reqeust):
       orders_qs = Orders.objects.all()
       order_json = OrderSerializer(orders_qs,many=True).data
       return Response(order_json)

@api_view(['GET'])
def PositionsApi(reqeust):
       positions_qs = models.Positions.objects.all()
       positions_json = serializers.PositionsSerializer(positions_qs,many=True).data
       return Response(positions_json)