from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from kiteconnect import KiteConnect
from django.conf import settings
import threading
from ..views import coreLogic, getPositions, total_pnl
from .. import constants
from ..models import AlgoWatchlist,Instruments
from .serializers import AlgoWatchlistSerializer, PreferencesSerializer, InstrumentsSerializer

kite = KiteConnect(api_key=constants.KITE_API_KEY)

coreLogicLock = threading.Lock()
coreRunning = False

kite = KiteConnect(api_key=constants.KITE_API_KEY)

@api_view(["POST", "GET"])
def login_view(request):
    # if request.medthod == "POST":
    
    if request.method == 'GET':
        if request.GET['request_token'] != "":
            print(request.GET['request_token'])
            data = kite.generate_session(
                request.GET['request_token'], api_secret=constants.KITE_API_SECRETE)
            kite.set_access_token(data["access_token"])
            coreLogic()
            return Response({'Data':"good"})


    return Response({"Data":"data"})

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
