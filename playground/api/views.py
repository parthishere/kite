from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from kiteconnect import KiteConnect
from django.conf import settings
import threading
import logging
from ..views import coreLogic, getPositions, total_pnl,login_in_zerodha
import pyotp
from ..models import AlgoWatchlist,Instruments
from .serializers import AlgoWatchlistSerializer, PreferencesSerializer, InstrumentsSerializer

kite = KiteConnect(api_key=settings.KITE_API_KEY)

coreLogicLock = threading.Lock()
coreRunning = False

kite = KiteConnect(api_key=settings.KITE_API_KEY)

@api_view(["GET"])
def login_view(request):    
        if 'request_token' in request.GET and request.GET.get('request_token'):
            data = kite.generate_session(
                request.GET['request_token'], api_secret=settings.KITE_API_SECRET)
            kite.set_access_token(data["access_token"])
            coreLogic()
            return Response({'Data':"good"})    

@api_view(['GET'])
def login_with_zerodha(request):            
        topt = pyotp.TOTP('ZF3MONJ23XF34ESGSGRXOKR6RGTRQLXN')
        toptKey = topt.now()        
        kite = login_in_zerodha(settings.KITE_API_KEY, settings.KITE_API_SECRET, 'LN7447', 'zzzzaaaa', toptKey)
        profile = kite.profile()
        print(profile)
        return ("success")

@api_view(["GET"])
def algowatch(request):
    # if request.medthod == "POST":
    
    if kite.access_token is None:
        return redirect("/")
    positionArray = getPositions()
    totalPNL = total_pnl() or 0
    algoWatchlistArray = AlgoWatchlist.objects.all()
    allInstruments = list(Instruments.objects.all(
    ).values_list('tradingsymbol', flat=True))
    return Response({'allInstruments': allInstruments, 'algoWatchlistArray': algoWatchlistArray, 'positionArray': positionArray, 'totalPNL': totalPNL})
