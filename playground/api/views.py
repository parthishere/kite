from rest_framework.decorators import api_view
from rest_framework.response import Response  
from rest_framework.views import APIView
from django.shortcuts import render, redirect
from django.conf import settings
import threading
import logging
from .. import views
import pyotp
from .. import models
from . import serializers
from datetime import datetime
from ..views import coreLogic,login_in_zerodha,updateSubscriberList,instrumentObjectToManualWatchlistObject,instrumentObjectToAlgoWatchlistObject
import pyotp
from .. import models
from . import serializers
import json
from .. import constants
from .. import consumers

from kiteconnect import KiteConnect

kite = views.kite

coreLogicLock = threading.Lock()
coreRunning = False



@api_view(["GET"])
def login_view(request):    
    if request.GET.get('request_token'):
        
        data = kite.generate_session(
            request.GET['request_token'], api_secret=constants.KITE_API_SECRETE)
        kite.set_access_token(data["access_token"])
        logging.warning("Access token===== %s", data["access_token"])
        consumers.startLiveConnection(str(kite.access_token))
        coreLogic()
        return Response({'Data':"good"})    
    else:
        return Response({"Data": "Not good"})


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
        
    if kite.access_token is None:
        return redirect("/")
    positionArray = views.getPositions()
    totalPNL = views.total_pnl() or 0
    algoWatchlistArray = models.AlgoWatchlist.objects.all()
    allInstruments = list(models.Instruments.objects.all(
    ).values_list('tradingsymbol', flat=True))
    return Response({'allInstruments': allInstruments, 'algoWatchlistArray': algoWatchlistArray, 'positionArray': positionArray, 'totalPNL': totalPNL})

@api_view(["GET"])
def manualwatch(request):
    if kite.access_token is None:
        return redirect("/")
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


# Directly called by frontend to start process
class StartAlgoAPI(APIView):
    def post(self,request):
        response = {'error':0,'status':''}
        try:            
            params = json.loads(request.body)                
            print("Came from JS to start" + params['script'])            
            models.AlgoWatchlist.objects.filter(instruments=params['script']).update(startAlgo=True)
            models.AlgoWatchlist.objects.filter(instruments=params['script']).update(qty=int(params['scriptQty']))        
            response = {'error':0,'status':'success'}
            return Response(json.dumps(response))
        except Exception as e:
            response = {'error':1,'status':str(e)}
            return Response(json.dumps(response))

class StopAlgoAPI(APIView):
    def post(self,request):
        response = {'error':0,'status':''}
        try:
            params = json.loads(request.body)
            print("Came from JS to stop" + params['script'])
            if 'isFromAlgoTest' in params and params['isFromAlgoTest'] == True:
                print("Stop Single from Algowatchlist")
                models.AlgoWatchlist.objects.filter(
                    instruments=params['script']).update(startAlgo=False)
                models.AlgoWatchlist.objects.filter(instruments=params['script']).update(
                    qty=int(params['scriptQty']))
            else:
                print("Stop Single from Manualwatchlist")
                models.ManualWatchlist.objects.filter(
                    instruments=params['script']).update(startAlgo=False)
                models.ManualWatchlist.objects.filter(
                    instruments=params['script']).update(isSellClicked=False)
                models.ManualWatchlist.objects.filter(
                    instruments=params['script']).update(isBuyClicked=False)
                models.ManualWatchlist.objects.filter(instruments=params['script']).update(
                    qty=int(params['scriptQty']))        
            response = {'error':0,'status':'success'}
            return Response(json.dumps(response))
        except Exception as e:
            response = {'error':1,'status':str(e)}
            return Response(json.dumps(response))

class StartAllAPI(APIView):
    def post(self,request):
        response = {'error':0,'status':''}
        try:
            params = json.loads(request.body)
            print("Came from JS to start All")
            algo_array = models.AlgoWatchlist.objects.all()
            print(len(algo_array))
            for items in algo_array:
                print("Starting for all items: ", items.instruments)
                models.AlgoWatchlist.objects.filter(instruments=items.instruments).update(startAlgo=True)
                models.AlgoWatchlist.objects.filter(instruments=items.instruments).update(qty=int(params['scriptQty']))
            response = {'error':0,'status':'success'}
            return Response(json.dumps(response))
        except Exception as e:
            response = {'error':1,'status':str(e)}
            return Response(json.dumps(response))

class BuySingleAPI(APIView):
    def post(self,request):
        response = {'error':0,'status':''}
        try:
            params = json.loads(request.body)            
            print("Came from JS to buy single" + params['script'])
            print("Came from JS to start" + params['scriptQty'])
            models.ManualWatchlist.objects.filter(instruments=params['script']).update(startAlgo=True)
            models.ManualWatchlist.objects.filter(instruments=params['script']).update(positionType="BUY")
            models.ManualWatchlist.objects.filter(instruments=params['script']).update(qty=int(params['scriptQty']))
            models.ManualWatchlist.objects.filter(instruments=params['script']).update(isBuyClicked=True)            
            response = {'error':0,'status':'success'}
            return Response(json.dumps(response))                            
        except Exception as e:
            response = {'error':1,'status':str(e)}
            return Response(json.dumps(response))
        
class SellSingle(APIView):
    def post(self,request):
        response = {'error':0,'status':''}
        try:
            params = json.loads(request.body)            
            print("Came from JS to sell single" + params['script'])
            print("Came from JS to start" + params['scriptQty'])
            models.ManualWatchlist.objects.filter(instruments=params['script']).update(startAlgo=True)
            models.ManualWatchlist.objects.filter(instruments=params['script']).update(positionType="SELL")
            models.ManualWatchlist.objects.filter(instruments=params['script']).update(qty=int(params['scriptQty']))
            models.ManualWatchlist.objects.filter(instruments=params['script']).update(isSellClicked=True)            
            response = {'error':0,'status':'success'}
            return Response(json.dumps(response))            
        except Exception as e:
            response = {'error':0,'status':str(e)}
            return Response(json.dumps(response))
        
class ScaleUpQtyAPI(APIView):
     def post(self,request):
        response = {'error':0,'status':''}
        try:
            params = json.loads(request.body)               
            script = params['script']
            qty = params['scriptQty']
            print("Updated QTY ===========+++++++", script, qty, params['isFromAlgoTest'])
            if 'isFromAlgoTest' in params and params['isFromAlgoTest'] == True:
                models.AlgoWatchlist.objects.filter(instruments=script).update(qty=qty)
            else:
                models.ManualWatchlist.objects.filter(instruments=script).update(qty=qty)                
            response = {'error':0,'status':'success'}
            return Response(json.dumps(response))
        except Exception as e:
            response = {'error':0,'status':str(e)}
            return Response(json.dumps(response))

class ScaleDownQtyAPI(APIView):
     def post(self,request):
        response = {'error':0,'status':''}
        try:
            params = json.loads(request.body)               
            script = params['script']
            qty = params['scriptQty']
            print("Updated QTY ===========+++++++", script, qty)
            if 'isFromAlgoTest' in params and params['isFromAlgoTest'] == True:
                models.AlgoWatchlist.objects.filter(instruments=script).update(qty=qty)
            else:
                models.ManualWatchlist.objects.filter(instruments=script).update(qty=qty)
            response = {'error':0,'status':'success'}
            return Response(json.dumps(response))
        except Exception as e:
            response = {'error':0,'status':str(e)}
            return Response(json.dumps(response))

class AddInstrumentAPI(APIView):
    def post(self,request):
        response = {'error':0,'status':''}
        try:
            params = json.loads(request.body)             
            print("Came from JS to Add Instrument ==============" + params['script'])
            script = params['script']
            flag = params['flag']
            instrumentObject = models.Instruments.objects.filter(tradingsymbol=script).values()
            instumentData = instrumentObject[0]
            print(instumentData["instrument_token"])
            print(instumentData["tradingsymbol"])
            updateSubscriberList(instumentData["instrument_token"], instumentData["tradingsymbol"], True)
            if flag == "ManualWatch":
                instrumentObjectToManualWatchlistObject(instrumentObject)
                manualWatchObject = models.ManualWatchlist.objects.filter(instruments=script).values()
                response = {'error':0,'status':'success','instrument':list(manualWatchObject)}
                return Response(json.dumps(response))                    
            elif flag == "AlgoWatch":
                instrumentObjectToAlgoWatchlistObject(instrumentObject)
                algoWatchObject = models.AlgoWatchlist.objects.filter(instruments=script).values()
                response = {'error':0,'status':'success','instrument':list(algoWatchObject)}
                return Response(json.dumps(response))                   
        except Exception as e:
            response = {'error':0,'status':str(e)}
            return Response(json.dumps(response))
            
class DeleteInstrumentAPI(APIView):
    def post(self,request):
        response = {'error':0,'status':''}
        try:
            params = json.loads(request.body)            
            script = params['script']
            flag = params['flag']
            if flag == "ManualWatch":
                models.ManualWatchlist.objects.filter(instruments=script).delete()
            elif flag == "AlgoWatch":
                models.AlgoWatchlist.objects.filter(instruments=script).delete()
            instrumentObject = models.Instruments.objects.filter(tradingsymbol=script).values()
            instumentData = instrumentObject[0]
            updateSubscriberList(instumentData["instrument_token"], instumentData["tradingsymbol"], False)
            response = {'error':0,'status':'success'}
            return Response(json.dumps(response))            
        except Exception as e:
            response = {'error':0,'status':str(e)}
            return Response(json.dumps(response))







## Error


