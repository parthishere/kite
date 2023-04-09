from rest_framework.decorators import api_view
from rest_framework.response import Response    
from django.shortcuts import render, redirect
from kiteconnect import KiteConnect
from django.conf import settings
import threading
import logging
from .. import views
import pyotp
from .. import models
from . import serializers
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
            Response({'Data':"not good"}) 
        views.coreLogic()
        return Response({'Data':"good"})    

@api_view(['GET'])
def algowatch(request):        
        algowatchlist = models.AlgoWatchlist.objects.all()
        for obj in algowatchlist:
               print(obj)
        return Response("No Response")
       
def login_with_zerodha(request):            
    topt = pyotp.TOTP('ZF3MONJ23XF34ESGSGRXOKR6RGTRQLXN')
    toptKey = topt.now()        
    kite = views.login_in_zerodha(settings.KITE_API_KEY, settings.KITE_API_SECRET, 'LN7447', 'zzzzaaaa', toptKey)
    profile = kite.profile()
    print(profile)
    return Response({"Status":"success"})


@api_view(["GET"])
def algowatch(request):
        
    # if kite.access_token is None:
    #     return redirect("/")
    positionArray = views.getPositions()
    totalPNL = views.total_pnl() or 0
    algoWatchlistArray = models.AlgoWatchlist.objects.all()
    allInstruments = list(models.Instruments.objects.all(
    ).values_list('tradingsymbol', flat=True))
    return Response({'allInstruments': allInstruments, 'algoWatchlistArray': algoWatchlistArray, 'positionArray': positionArray, 'totalPNL': totalPNL})

@api_view(["GET"])
def manualwatch(request):
    # if kite.access_token is None:
    #     return redirect("/")
    positionArray = views.getPositions()
    totalPNL = views.total_pnl()
    manualWatchlistArray = models.ManualWatchlist.objects.all()
    allInstruments = list(models.Instruments.objects.all(
    ).values_list('tradingsymbol', flat=True))
    return Response({'allInstruments': allInstruments, 'manualWatchlistArray': manualWatchlistArray, 'positionArray': positionArray, 'totalPNL': totalPNL})

@api_view(['GET'])
def OrdersApi(reqeust):
       orders_qs = models.Orders.objects.all()
       order_json = serializers.OrderSerializer(orders_qs,many=True).data
       return Response(order_json)

@api_view(["GET", "POST"])
def settings_view(request):
    if kite.access_token is None:
        return redirect("/")
    
    if request.method == "GET":
        if models.Preferences.objects.filter(scriptName="Default").exists():
            obj = models.Preferences.objects.filter(scriptName="Default")
            serializer = models.PreferencesSerializer(obj).data
        else:
            return Response({"status":406, "data":{"error": "No Default settings found, create settings first"}})
        return Response(serializer)
    
    if request.method == "POST":
        time = datetime.strptime(request.POST.get('time'), '%H:%M:%S')
        stoploss = request.POST.get('stoploss')
        target = request.POST.get('target')
        scaleupqty = request.POST.get('scaleupqty')
        scaledownqty = request.POST.get('scaledownqty')
        openingrange = request.POST.get('openingrange')
        openingrangebox = request.POST.get('openingrangebox')
        try:
            if models.Preferences.objects.filter(scriptName="Default").exists():
                models.Preferences.objects.filter(scriptName="Default").update(time=time, stoploss=stoploss, target=target,
                                                                        scaleupqty=scaleupqty, scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
            else:
                settings = models.Preferences(scriptName="Default", time=time, stoploss=stoploss, target=target, scaleupqty=scaleupqty,
                                    scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
                settings.save()
                
        except:
            return Response({"status": "500" ,"data": {"error":"Some error occured while saving the object on server"}})
        return Response({"status":200, 'data': "updated/created"})

@api_view(['GET'])
def PositionsApi(reqeust):
       positions_qs = models.Positions.objects.all()
       positions_json = serializers.PositionsSerializer(positions_qs,many=True).data
       return Response(positions_json)

       

