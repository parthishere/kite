from rest_framework.decorators import api_view
from rest_framework.response import Response    
from django.shortcuts import render, redirect
from kiteconnect import KiteConnect
from django.conf import settings
import threading
import logging
from ..views import coreLogic,login_in_zerodha
import pyotp
from ..models import AlgoWatchlist,Instruments, ManualWatchlist
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
    return Response({"Status":"success"})


@api_view(["GET"])
def algowatch(request):
        
    # if kite.access_token is None:
    #     return redirect("/")
    positionArray = getPositions()
    totalPNL = total_pnl() or 0
    algoWatchlistArray = AlgoWatchlist.objects.all()
    allInstruments = list(Instruments.objects.all(
    ).values_list('tradingsymbol', flat=True))
    return Response({'allInstruments': allInstruments, 'algoWatchlistArray': algoWatchlistArray, 'positionArray': positionArray, 'totalPNL': totalPNL})

@api_view(["GET"])
def manualwatch(request):
    # if kite.access_token is None:
    #     return redirect("/")
    positionArray = getPositions()
    totalPNL = total_pnl()
    manualWatchlistArray = ManualWatchlist.objects.all()
    allInstruments = list(Instruments.objects.all(
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
        if Preferences.objects.filter(scriptName="Default").exists():
            obj = Preferences.objects.filter(scriptName="Default")
            serializer = PreferencesSerializer(obj).data
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
            if Preferences.objects.filter(scriptName="Default").exists():
                Preferences.objects.filter(scriptName="Default").update(time=time, stoploss=stoploss, target=target,
                                                                        scaleupqty=scaleupqty, scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
            else:
                settings = Preferences(scriptName="Default", time=time, stoploss=stoploss, target=target, scaleupqty=scaleupqty,
                                    scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
                settings.save()
                
        except:
            return Response({"status": "500" ,"data": {"error":"Some error occured while saving the object on server"}})
        return Response({"status":200, 'data': "updated/created"})

       

