from rest_framework.decorators import api_view
from rest_framework.response import Response  
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.views import APIView
from django.conf import settings
import threading
import logging
from .. import views
import pyotp
from .. import models
from . import serializers
from datetime import datetime, timedelta
from ..views import coreLogic,login_in_zerodha,updateSubscriberList,instrumentObjectToManualWatchlistObject,instrumentObjectToAlgoWatchlistObject
import pyotp
from .. import models
from . import serializers
import json
from .. import constants
from .. import consumers
from .permissions import CustomPermission
from rest_framework.permissions import AllowAny
import django_filters.rest_framework
from rest_framework import filters

kite = views.kite

coreLogicLock = threading.Lock()
coreRunning = False

@api_view(["GET"])
def login_view(request):  
    """ 
    Send request_token in the request.GET as a GET parameter so basically :
    url/api/login?request_token=ARE123FDSA
    
    @param: request_token
    """
    response = {'error':0,'status':'', "data":""}  
    try:
        if request.GET.get('request_token'):
            
            data = kite.generate_session(
                request.GET['request_token'], api_secret=constants.KITE_API_SECRETE)
            kite.set_access_token(data["access_token"])
            logging.warning("Access token===== %s", data["access_token"])
            
            consumers.startLiveConnection(str(kite.access_token))
            coreLogic()
            
            TimeObjData = models.DateTimeCheck.objects.all()
            if TimeObjData.exists():
                TimeObj = TimeObjData.first()
                todayDate = (datetime.now() + timedelta(hours=5, minutes=30)).date()
                if TimeObj.dateCheck != todayDate:
                    TimeObjData.update(dateCheck=todayDate)
                    views.clearAllData()
                    print("inside the chekc")
                    views.fetchInstrumentInBackground()
                    
            algoWatchlistArray = models.AlgoWatchlist.objects.all()
            manualWatchlistArray = models.ManualWatchlist.objects.all()
            views.updateSavedSubscriberList(algoWatchlistArray.values())
            views.updateSavedSubscriberList(manualWatchlistArray.values())
            
            response['error'] = 0
            response['status'] = "success"
            response["data"] = "User Authenticated."
            return Response(response)    
        else:
            response['error'] = 1
            response['status'] = "error"
            response["data"] = "User not Authenticated..Try again"
            return Response(response)
    except:
        response['error'] = 1
        response['status'] = "error"
        response["data"] = "User not Authenticated..Try again"
        return Response(response)
        
    
@api_view(["GET"])   
def logoutUser(request):
    response = {'error':0,'status':'', "data":""}
    print(kite.access_token )
    try:
        # views.download_thread.stop()
        print("before token")
        print(kite.access_token)
        
        
        views.stop_threads = True
        # if download_thread:
        #     download_thread.join()
        views.timer.cancel()
        
        kite.invalidate_access_token()
        kite.set_access_token(None)
        
        print("after token")
        print(kite.access_token)
        response['error'] = 0
        response['status'] = "success"
        response["data"] = "User UnAuthenticated, please log back in..."
        return Response(response)     
    except Exception as e:
        response['error'] = 1
        response['status'] = "error"
        response["data"] = str(e)
        return Response(response)  


@api_view(["GET"])
def login_check_view(request):   
    response = {'error':0,'status':'', "data":""}
    print(kite.access_token )
    if kite.access_token: 
        response['error'] = 0
        response['status'] = "success"
        response["data"] = "User Authenticated"
        return Response(response)    
    else:
        response['error'] = 0
        response['status'] = "fail"
        response["data"] = "User not Authenticated."
        return Response(response)

       
def login_with_zerodha(request):          
    response = {'error':0,'status':'', "data":""}  
    topt = pyotp.TOTP('ZF3MONJ23XF34ESGSGRXOKR6RGTRQLXN')
    toptKey = topt.now()        
    kite = views.login_in_zerodha(settings.KITE_API_KEY, settings.KITE_API_SECRET, 'LN7447', 'zzzzaaaa', toptKey)
    profile = kite.profile()
    print(profile)
    response['error'] = 1
    response['status'] = "error"
    response["data"] = "Not valid parameters"
    return Response(response)

@api_view(["GET"])
def allInstuments(request):
    """
    
    repsonse : {
    "error": 0,
    "status": "success",
    "data": {
        "allInstruments": [
            {
                "name": "NIFTY22DEC14000CE"
            },
            {
                "name": "NIFTY22DEC10900PE"
            },
        ]
    }
    }
    """
    allInstruments = []
    for x in  models.Instruments.objects.all().values_list('tradingsymbol', flat=True):
        allInstruments.append({"name": x})
    return Response({"error":0, "status": "success", "data":{"allInstruments":allInstruments}})


@api_view(["GET"])
def algowatch(request):
    response = {'error':0,'status':'', "data":""}
    if not kite.access_token :
        response['error'] = 1
        response['status'] = "error"
        response["data"] = "User not Authenticated..Please log in"
        return Response(response)
    positionArray = views.getPositions()
    positionData = serializers.PositionsSerializer(positionArray, many=True).data
    totalPNL = views.total_pnl() or 0
    algoWatchlistArray = models.AlgoWatchlist.objects.all()
    algoData = serializers.AlgoWatchlistSerializer(algoWatchlistArray, many=True).data
    # allInstruments = list(models.Instruments.objects.all(
    # ).values_list('tradingsymbol', flat=True))
    return Response({"error":0, "status": "success", "data":{'algoWatchlistArray': algoData, 'positionArray': positionData, 'totalPNL': totalPNL}})

@api_view(["GET"])
def manualwatch(request):
    response = {'error':0,'status':'', "data":""}
    if not kite.access_token:
        response['error'] = 1
        response['status'] = "error"
        response["data"] = "User not Authenticated..Please log in"
        return Response(response)
    positionArray = views.getPositions()
    positionData = serializers.PositionsSerializer(positionArray, many=True).data
    totalPNL = views.total_pnl()
    manualWatchlistArray = models.ManualWatchlist.objects.all()
    manual_data = serializers.ManualWatchlistSerializer(manualWatchlistArray, many=True).data
    # allInstruments = list(models.Instruments.objects.all(
    # ).values_list('tradingsymbol', flat=True))
    return Response({"error":0, "status": "success", "data":{'manualWatchlistArray': manual_data, 'positionArray': positionData, 'totalPNL': totalPNL}})

@api_view(['GET'])
def OrdersApi(reqeust):
    response = {'error':0,'status':'', "data":""}
    if not kite.access_token:
        response['error'] = 1
        response['status'] = "error"
        response["data"] = "User not Authenticated..Please log in"
        return Response(response) 
    orders = kite.orders()

    for order in orders:
        print(order)
        if not views.order_exists(order['order_id']):
            orderObject = models.Orders(instruments=order['tradingsymbol'], qty=order['quantity'],
                                 status=order['status'], avgTradedPrice=order['average_price'], instrumentsToken=order['instrument_token'],
                                 orderTimestamp=order['order_timestamp'], orderType=order[
                                     'order_type'], transactionType=order['transaction_type'],
                                 product=order['product'], orderId=order['order_id'])
            orderObject.save()
    order_json = serializers.OrderSerializer(models.Orders.objects.all(),many=True).data
    return Response({"error":0,"status":"success","data":{"orders":order_json}})



@api_view(["GET","POST"])
def SettingsView(request):
    """ Send Intrument time (%H:%M:%S format), stoploss, target, scaleupqty, scaledownqty, openingrange and openingrangebox in the request.body as a json response 
    @param: "time"
    @param: "stoploss"
    @param: "target"
    @param: "scaleupqty"
    @param: "scaledownqty"
    @param: "openingrange"
    @param: "openingrangebox"
    
    
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    const data = {
        "time":currentTime, // Trading Symbol
        "stoploss":0.2, // float
        "target": 1.0, // float
        "scaleupqty":1, // integer
        "scaledownqty":1, //integer
        "openingrange":10.0, // float
        "openingrangebox":false, // boolean       
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    
    .then(response => response.json())
    
  
    
    example:
    
    "time":"TCS", // Trading Symbol
    "stoploss":0.2, // float
    "target": 1.0, // float
    "scaleupqty":1, // integer
    "scaledownqty":1, //integer
    "openingrange":10.0, // float
    "openingrangebox":false, // boolean
    """
    response = {'error':0,'status':'', "data":""}
    if not kite.access_token:
        response['error'] = 1
        response['status'] = "error"
        response["data"] = "User not Authenticated..Please log in"
        return Response(response)

    try:
        if request.method == "POST":
            params = json.loads(request.body)
            time = datetime.strptime(params.get('time'), '%H:%M:%S')
            stoploss = params.get('stoploss')
            target = params.get('target')
            scaleupqty = params.get('scaleupqty')
            scaledownqty = params.get('scaledownqty')
            openingrange = params.get('openingrange')
            openingrangebox = params.get('openingrangebox')
            if views.settings_exists():
                models.Preferences.objects.filter(scriptName="Default").update(time=time, stoploss=stoploss, target=target,
                                                                        scaleupqty=scaleupqty, scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
            else:
                settings = models.Preferences(scriptName="Default", time=time, stoploss=stoploss, target=target, scaleupqty=scaleupqty,
                                    scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
                settings.save()
            
            response['error'] = 0
            response['status'] = "success"
            response["data"] = 'Preference updated successfully!'
            return Response(response)
        else:
            settingsValues = models.Preferences.objects.all()
            json_data = serializers.PreferencesSerializer(settingsValues, many=True).data
            response['error'] = 0
            response['status'] = "success"
            response["data"] = {"settings":json_data}
            return Response(response)
        
            
    except Exception as e:
        response['error'] = 1
        response['status'] = "error"
        response["data"] = str(e)
        return Response(response)
    
    # if not kite.access_token :
    #     return Response({"Data": "User not Authenticated..Please log in "})
    
    # if request.method == "GET":
    #     if models.Preferences.objects.filter(scriptName="Default").exists():
    #         obj = models.Preferences.objects.filter(scriptName="Default")
    #         serializer = serializers.PreferencesSerializer(obj).data
    #     else:
    #         return Response({"status":406, "data":{"error": "No Default settings found, create settings first"}})
    #     return Response(serializer)
    
    # if request.method == "POST":
    #     time = datetime.strptime(request.POST.get('time'), '%H:%M:%S')
    #     stoploss = request.POST.get('stoploss')
    #     target = request.POST.get('target')
    #     scaleupqty = request.POST.get('scaleupqty')
    #     scaledownqty = request.POST.get('scaledownqty')
    #     openingrange = request.POST.get('openingrange')
    #     openingrangebox = request.POST.get('openingrangebox')
    #     try:
    #         if models.Preferences.objects.filter(scriptName="Default").exists():
    #             models.Preferences.objects.filter(scriptName="Default").update(time=time, stoploss=stoploss, target=target,
    #                                                                     scaleupqty=scaleupqty, scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
    #         else:
    #             settings = models.Preferences(scriptName="Default", time=time, stoploss=stoploss, target=target, scaleupqty=scaleupqty,
    #                                 scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
    #             settings.save()
                
    #     except:
    #         return Response({"status": "500" ,"data": {"error":"Some error occured while saving the object on server"}})
    #     return Response({"status":200, 'data': "updated/created"})

@api_view(['GET'])
def PositionsModelApi(reqeust):
    response = {'error':0,'status':'', "data":""}
    if not kite.access_token :
        response['error'] = 1
        response['status'] = "error"
        response["data"] = "User not Authenticated..Please log in "
        return Response(response)
    positions_qs = models.Positions.objects.all()
    positions_json = serializers.PositionsSerializer(positions_qs,many=True).data
    return Response({"error":0,"status":"success","data":{"postions":positions_json}})


# Directly called by frontend to start process
class StartAlgoSingleAPI(APIView):
    """ Send Intrument name (TCS) and quantity in the request.body as a json response 
    @param: "instument"
    @param: "instrumentQuantity"
    
    const data = {
        "instrument":"TCS", // Trading Symbol
        "instrumentQuantity":1,
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    
    .then(response => response.json())
    
  
    
    example:
    
    "instrument":"TCS", // Trading Symbol
    "instrumentQuantity":1, // int
    
    """
    def post(self,request):
        response = {'error':0,'status':'', "data":""}
        if not kite.access_token :
            response['error'] = 1
            response['status'] = "error"
            response["data"] = "User not Authenticated..Please log in"
            return Response(response) 
        try:     
            params = json.loads(request.body)       
            instrument_name = params.get("instrument")   
            instrument_quantity = params.get("instrumentQuantity") 
            if instrument_name and instrument_quantity: 
                print(instrument_name)  
                # print("Came from JS to start" + params['instruments'])            
                models.AlgoWatchlist.objects.filter(instruments=instrument_name).update(entryprice=0.0 , slHitCount = 0)
                models.AlgoWatchlist.objects.filter(instruments=instrument_name).update(startAlgo=True, algoStartTime=datetime.utcnow())
                models.AlgoWatchlist.objects.filter(instruments=instrument_name).update(qty=instrument_quantity)
               
                response['error'] = 0      
                response['status'] = 'success'
                response["data"] = "algo watch started"
                return Response(response)
            else:
                response['error'] = 1
                response['status'] = "error"
                response["data"] = "Not valid parameters"
                return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = "error"
            response["data"] = str(e)
            return Response(response) 


class StopAlgoAndManualSingleAPI(APIView):
    """ Send Intrument name (TCS) ,quantity and is_algo in the request.body as a json response 
    @param: "instument"
    @param: "instrumentQuantity"
    @param: "is_algo"
    
    const data = {
        "instrument":"TCS", // Trading Symbol
        "instrumentQuantity":1,
        "is_algo": true // means manual instrument will be automaticaly set to false
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    .then(response => response.json())
    
    
    example:
    
    "instrument":"TCS", // Trading Symbol
    "instrumentQuantity":1,
    "is_algo": true // means manual instrument will be automaticaly set to false
    
    
    """
    def post(self,request):
        response = {'error':0,'status':'', "data":""}
        if not kite.access_token :
            response['error'] = 1
            response['status'] = "error"
            response["data"] = "User not Authenticated..Please log in "
            return Response(response)
            
        try:
            params = json.loads(request.body)               
            instrument_name = params['instrument']
            instrument_quantity = params['instrumentQuantity']
            is_algo = params["is_algo"] 
            if instrument_name and instrument_quantity and is_algo:
                if is_algo == True or is_algo == "true" or is_algo == 1:
                    print("Stop Single from Algowatchlist")
                    models.AlgoWatchlist.objects.filter(
                        instruments=instrument_name).update(startAlgo=False)
                    models.AlgoWatchlist.objects.filter(instruments=instrument_name).update(
                        qty=instrument_quantity)
                else:
                    print("Stop Single from Manualwatchlist")
                    models.ManualWatchlist.objects.filter(
                        instruments=instrument_name).update(startAlgo=False)
                    models.ManualWatchlist.objects.filter(
                        instruments=instrument_name).update(isSellClicked=False)
                    models.ManualWatchlist.objects.filter(
                        instruments=instrument_name).update(isBuyClicked=False)
                    models.ManualWatchlist.objects.filter(instruments=instrument_name).update(
                        qty=instrument_quantity)
                    
                response['error'] = 0     
                response['status'] = 'success'
                response['data'] = 'algowatch/manualwatch stopped'
                return Response(response)
            else:
                response['error'] = 1
                response['status'] = "error"
                response["data"] = "Not valid parameters"
                return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = "error"
            response["data"] = str(e)
            return Response(response)





class StartAllAPI(APIView):
    """ 
    @instrumentQuantity in request.body as a json response 
    """
    def post(self,request):
        response = {'error':0,'status':'', "data":""}
        if not kite.access_token :
            response['error'] = 1
            response['status'] = "error"
            response["data"] = "User not Authenticated..Please log in "
            return Response(response)
        try:
            params = json.loads(request.body)               
            instrument_quantity = params['instrumentQuantity']
            print("Came from JS to start All")
            if instrument_quantity:
                algo_array = models.AlgoWatchlist.objects.all()
                print(len(algo_array))
                for items in algo_array:
                    print("Starting for all items: ", items.instruments)
                    models.AlgoWatchlist.objects.filter(instruments=items.instruments).update(startAlgo=True)
                    models.AlgoWatchlist.objects.filter(instruments=items.instruments).update(qty=instrument_quantity)
                response['error'] = 0      
                response['status'] = 'success'
                response["data"] = "Started for all Algowatch items"
                return Response(response)
            else:
                response['error'] = 1
                response['status'] = "error"
                response["data"] = "Not valid parameters"
                return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = "error"
            response["data"] = str(e)
            return Response(response)

class BuySingleManualAPI(APIView):
    """ Send Intrument name (TCS) and quantity  in the request.body as a json response 
    @param: "instument"
    @param: "instrumentQuantity"
    
    const data = {
        "instrument":"TCS", // Trading Symbol
        "instrumentQuantity":1,
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    
    .then(response => response.json())
    
    example:
    
    "instrument":"TCS", // Trading Symbol
    "instrumentQuantity":1,
    
    """
    def post(self,request):
        response = {'error':0,'status':'', "data":""}
        if not kite.access_token :
            response['error'] = 1
            response['status'] = "error"
            response["data"] = "User not Authenticated..Please log in "
            return Response(response)
        try:
            params = json.loads(request.body)               
            instrument_name = params['instrument']
            instrument_quantity = params['instrumentQuantity']
            if instrument_name and instrument_quantity:
                models.ManualWatchlist.objects.filter(instruments=instrument_name).update(startAlgo=True)
                models.ManualWatchlist.objects.filter(instruments=instrument_name).update(positionType="BUY")
                models.ManualWatchlist.objects.filter(instruments=instrument_name).update(qty=instrument_quantity)
                models.ManualWatchlist.objects.filter(instruments=instrument_name).update(isBuyClicked=True)            
                response['error'] = 0      
                response['status'] = 'success'
                response["data"] = "Bought Single Instument for Manualwatch"
                return Response(response)
            else:
                response['error'] = 1
                response['status'] = "error"
                response["data"] = "Not valid parameters"
                return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = "error"
            response["data"] = str(e)
            return Response(response)
        
        
class SellSingleManualAPI(APIView):
    """ Send Intrument name (TCS) and quantity  in the request.body as a json response 
    @param: "instument"
    @param: "instrumentQuantity"
    
    const data = {
        "instrument":"TCS", // Trading Symbol
        "instrumentQuantity":1,
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    
    .then(response => response.json())
    
    example:
    
    "instrument":"TCS", // Trading Symbol
    "instrumentQuantity":1,
    
    
    """
    def post(self,request):
        response = {'error':0,'status':'', "data":""}
        if not kite.access_token :
            response['error'] = 1
            response['status'] = "error"
            response["data"] = "User not Authenticated..Please log in "
            return Response(response)
        try:         
            params = json.loads(request.body) 
            instrument_name = params['instrument']
            instrument_quantity = params['instrumentQuantity']

            if instrument_name and instrument_quantity:
                models.ManualWatchlist.objects.filter(instruments=instrument_name).update(startAlgo=True)
                models.ManualWatchlist.objects.filter(instruments=instrument_name).update(positionType="SELL")
                models.ManualWatchlist.objects.filter(instruments=instrument_name).update(qty=instrument_quantity)
                models.ManualWatchlist.objects.filter(instruments=instrument_name).update(isSellClicked=True)            
                response['error'] = 0      
                response['status'] = 'success'
                response["data"] = "sold Manual watchlist instrument item"
                return Response(response)
            else:
                response['error'] = 1
                response['status'] = "error"
                response["data"] = "Not valid parameters"
                return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = "error"
            response["data"] = str(e)
            return Response(response)
       
        
class ScaleUpQtyAPI(APIView):
    """ Send Intrument name (TCS) ,quantity and is_algo in the request.body as a json response 
    @param: "instument"
    @param: "instrumentQuantity"
    @param: "is_algo"
    
    const data = {
        "instrument":"TCS", // Trading Symbol
        "instrumentQuantity":1,
        "is_algo": true // means manual instrument will be automaticaly set to false
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    
    .then(response => response.json())
    
    example:
    
    "instrument":"TCS", // Trading Symbol
    "instrumentQuantity":1,
    "is_algo": true // means manual instrument will be automaticaly set to false
    
    """
    def post(self,request):
        response = {'error':0,'status':'', "data":""}
        if not kite.access_token :
            response['error'] = 1
            response['status'] = "error"
            response["data"] = "User not Authenticated..Please log in "
            return Response(response)
        try:
            params = json.loads(request.body) 
            instrument_name = params['instrument']
            instrument_quantity = params['instrumentQuantity']
            is_algo = params["is_algo"]
            
            if instrument_name and instrument_quantity and is_algo:
                print("Updated QTY ===========+++++++", instrument_name, instrument_quantity, is_algo)
                if is_algo == True or is_algo == "true" or is_algo == 1:
                    models.AlgoWatchlist.objects.filter(instruments=instrument_name).update(qty=instrument_quantity)
                else:
                    models.ManualWatchlist.objects.filter(instruments=instrument_name).update(qty=instrument_quantity)                
                response['error'] = 0      
                response['status'] = 'success'
                response["data"] = "scaled up quantity for algowatch/manualwatch list"
                return Response(response)
            else:
                response['error'] = 1
                response['status'] = "error"
                response["data"] = "Not valid parameters"
                return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = "error"
            response["data"] = str(e)
            return Response(response)

class ScaleDownQtyAPI(APIView):
    """ Send Intrument name (TCS) ,quantity and is_algo in the request.body as a json response 
    @param: "instument"
    @param: "instrumentQuantity"
    @param: "is_algo"
    
    const data = {
        "instrument":"TCS", // Trading Symbol
        "instrumentQuantity":1,
        "is_algo": true // means manual instrument will be automaticaly set to false
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    
    .then(response => response.json())
    
    example:
    
    "instrument":"TCS", // Trading Symbol
    "instrumentQuantity":1,
    "is_algo": true // means manual instrument will be automaticaly set to false
    
    """
    def post(self,request):
        response = {'error':0,'status':'', "data":""}
        if not kite.access_token :
            response['error'] = 1
            response['status'] = "error"
            response["data"] = "User not Authenticated..Please log in "
            return Response(response)
        try:
            params = json.loads(request.body)               
            instrument_name = params['instrument']
            instrument_quantity = params['instrumentQuantity']
            is_algo = params["is_algo"]
            
            print("Updated QTY ===========+++++++", instrument_name, instrument_quantity)
            if is_algo == True or is_algo == "true" or is_algo == 1:
                models.AlgoWatchlist.objects.filter(instruments=instrument_name).update(qty=instrument_quantity)
            else:
                models.ManualWatchlist.objects.filter(instruments=instrument_name).update(qty=instrument_quantity)
            response['error'] = 0      
            response['status'] = 'success'
            response["data"] = "scaled down quantity for algowatch/manualwatch list"
            return Response(response)
            
        except Exception as e:
            response['error'] = 1
            response['status'] = "error"
            response["data"] = str(e)
            return Response(response)


## Ahithi baki 6e API banavva ni\
@api_view(["GET"])    
def searchAPI(request):
    """
    It will send all the instruments trading symbol starting from instrument data 
    @param: "q"
    @request: GET
    example:
    /search/?q="T" // will return all the instruments starting from T
    """
    
    q = request.query_params.get("q")
    instrumentObject = models.Instruments.objects.filter(
                tradingsymbol__startswith=q).values_list("id", "tradingsymbol")
  
    return Response({"error":0, "status":"sucess", "data":list(instrumentObject)})


class AddInstrumentAPI(APIView):
    """
    
    Send Intrument name (TCS) ,quantity and is_algo in the request.body as a json response 
    @param: "instument"
    @param: "is_algo"
    
    const data = {
        "instrument":"TCS", // Trading Symbol
        "is_algo": true // means manual instrument will be automaticaly set to false
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    
    .then(response => response.json())
    

    
    example:

    "instrument":"TCS", // Trading Symbol
    "is_algo": true // means manual instrument will be automaticaly set to false

   
    
    """
    def post(self,request):
        response = {'error':0,'status':'', "data":""}
        if not kite.access_token :
            response['error'] = 1
            response['status'] = "error"
            response["data"] = "User not Authenticated..Please log in "
            return Response(response)
        try:
            params = json.loads(request.body)             
            instrument_name = params['instrument']
            is_algo = params['is_algo']
            if instrument_name and is_algo:
                instrumentObject = models.Instruments.objects.filter(
                    tradingsymbol=instrument_name).values()
                print(instrumentObject)
                instumentData = instrumentObject[0]
                print(instumentData["instrument_token"])
                print(instumentData["tradingsymbol"])
                consumers.updateSubscriberList(
                    instumentData["instrument_token"], instumentData["tradingsymbol"], True)
                if is_algo == True or is_algo == "true" or is_algo == 1:
                    instrumentObjectToAlgoWatchlistObject(instrumentObject)
                    algoWatchObject = models.AlgoWatchlist.objects.filter(
                        instruments=instrument_name).values()
                    return Response({"error":0, "status":"success","data":{"instrument": list(algoWatchObject)}})
                    
                else:
                    instrumentObjectToManualWatchlistObject(instrumentObject)
                    manualWatchObject = models.ManualWatchlist.objects.filter(
                        instruments=instrument_name).values()
                    return Response({"error":0, "status":"success","data":{"instrument": list(manualWatchObject)}})
                    
            else:
                response['error'] = 1
                response['status'] = "error"
                response["data"] = "Not valid parameters"
                return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = "error"
            response["data"] = str(e)
            return Response(response)
            
class DeleteInstrumentAPI(APIView):
    """ Send Intrument name (TCS) ,quantity and is_algo in the request.body as a json response 
    @param: "instument"
    @param: "is_algo"
    
    const data = {
        "instrument":"TCS", // Trading Symbol
        "is_algo": true // means manual instrument will be automaticaly set to false
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    
    .then(response => response.json())
    

    
    example:
    
    "instrument":"TCS", // Trading Symbol
    "is_algo": true // means manual instrument will be automaticaly set to false
    
    
    """
    def post(self,request):
        response = {'error':0,'status':'', "data":""}
        if not kite.access_token :
            response['error'] = 1
            response['status'] = "error"
            response["data"] = "User not Authenticated..Please log in "
            return Response(response) 
        try:
            params = json.loads(request.body)             
            instrument_name = params['instrument']
            is_algo = params['is_algo']
            if instrument_name and is_algo:
                if is_algo == True or is_algo == "true" or is_algo == 1:
                    models.AlgoWatchlist.objects.filter(instruments=instrument_name).delete()
                else:
                    models.ManualWatchlist.objects.filter(instruments=instrument_name).delete()

                instrumentObject = models.Instruments.objects.filter(
                    tradingsymbol=instrument_name).values()
                instumentData = instrumentObject[0]
                updateSubscriberList(
                    instumentData["instrument_token"], instumentData["tradingsymbol"], False)
                response['error'] = 0
                response['status'] = "success"
                response["data"] = "Removed instrument from algowatch/manualwatch"
                return Response(response)
            else:
                response['error'] = 1
                response['status'] = "error"
                response["data"] = "Not valid parameters"
                return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = "error"
            response["data"] = str(e)
            return Response(response)


def position_exists(tradingsymbol):
    return models.Positions.objects.filter(instruments=tradingsymbol).exists()



def stopSinglehalfAPI(request):  # For Manual and Algo watchlist
    """ Send Intrument name (TCS) in the request.body as a json response 
    @param: "instument"
    
    const data = {
        "instrument":"TCS", // Trading Symbol
        "
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    
    .then(response => response.json())
    

    
    example:
    
    "instrument":"TCS", // Trading Symbol
    
    """
    response = {'error':0,'status':'', "data":""}
    if not kite.access_token :
        response['error'] = 1
        response['status'] = "error"
        response["data"] = "User not Authenticated..Please log in "
        return Response(response) 
    try:
        params = json.loads(request.body)
        # print("++++++++++++++++++++++++Algowatchlist Positions++++++++++++++++")
        algoArray = models.AlgoWatchlist.objects.all()
        # print(algoArray, "++++++++++++++++Algo Array Values=============")

        # Get value from Settings
        settings = models.Preferences.objects.all()
        # TG : Get % value from settings
        tg = settings.values()[0]['target']
        # SL : Get % value from settings
        sl = settings.values()[0]['stoploss']
        # TIME : Get seconds value from settings
        startTime = settings.values()[0]['time']
        # OR : Get % value from settings and of difference from CMP to OPEN
        ordp = settings.values()[0]['openingrange']
        # ORD :  Get true of fale from Settings to apply ORD or not
        ordtick = settings.values()[0]['openingrangebox']
        # 1. Run a loog for all watchlist items

        acriptttt = params['instrument']

        if acriptttt in consumers.liveData:
            liveValues = consumers.liveData[acriptttt]
            # UBL : #then UBL(Upper band limit)) is 2448 (2% of 2400, 2400 + 48 = 2448)
            partValue = (ordp*liveValues['Open'])/100
            ubl = liveValues['Open'] + partValue
            # LBL : #then LBL(Lower band limit)) is 2352 (2% of 2400, 2400 - 48 = 2352)
            lbl = liveValues['Open'] - partValue

        postions = models.Positions.objects.filter(instruments=acriptttt)
        potionObject = postions.values()[0]
        setQty = abs(potionObject['qty'])
        print('..........................setQty......... 1' , setQty)
        if -1<=setQty<=1:
            setQty = setQty
        else:
            setQty = int(setQty/2)
        print('..........................setQty......... 2' , setQty)

        if potionObject['positionType'] == "BUY":
            print(setQty,'SCRIPT QUANTITY=========================', 'BUY')
            views.tradeInitiateWithSLTG(type="SELL", scriptQty=setQty, exchangeType='NSE', sl=sl, tg=tg,
                                    ltp=liveValues['LTP'], scriptCode=acriptttt, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)
        if potionObject['positionType'] == "SELL":
            print(setQty,'SCRIPT QUANTITY=========================', 'SELL')
            views.tradeInitiateWithSLTG(type="BUY", scriptQty=setQty, exchangeType='NSE', sl=sl, tg=tg,
                                    ltp=liveValues['LTP'], scriptCode=acriptttt, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)

        response['error'] = 0
        response['status'] = "success"
        response["data"] = "Removed instrument from algowatch/manualwatch"
        return Response(response)
    except Exception as e:
        response['error'] = 1
        response['status'] = "error"
        response["data"] = str(e)
        return Response(response)


def stopSinglehalf_halfAlgo_manualAPI(request):  # For Manual and Algo watchlist
    """ Send Intrument name (TCS) in the request.body as a json response 
    @param: "instument"
    
    const data = {
        "instrument":"TCS", // Trading Symbol
    }
    
    fetch("URI", {
        method:"POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringyfy(data)
    })
    
    .then(response => response.json())
    

    
    example:
    
    "instrument":"TCS", // Trading Symbol
    
    
    """
    response = {'error':0,'status':'', "data":""}
    if not kite.access_token :
        response['error'] = 1
        response['status'] = "error"
        response["data"] = "User not Authenticated..Please log in "
        return Response(response) 
    try:
        params = json.loads(request.body)
        
        # print("++++++++++++++++++++++++Algowatchlist Positions++++++++++++++++")
        algoArray = models.ManualWatchlist.objects.all()
        # print(algoArray, "++++++++++++++++Algo Array Values=============")

        # Get value from Settings
        settings = models.Preferences.objects.all()
        # TG : Get % value from settings
        tg = settings.values()[0]['target']
        # SL : Get % value from settings
        sl = settings.values()[0]['stoploss']
        # TIME : Get seconds value from settings
        startTime = settings.values()[0]['time']
        # OR : Get % value from settings and of difference from CMP to OPEN
        ordp = settings.values()[0]['openingrange']
        # ORD :  Get true of fale from Settings to apply ORD or not
        ordtick = settings.values()[0]['openingrangebox']
        # 1. Run a loog for all watchlist items

        acriptttt = params['instrument']

        if acriptttt in consumers.liveData:
            liveValues = consumers.liveData[acriptttt]
            # UBL : #then UBL(Upper band limit)) is 2448 (2% of 2400, 2400 + 48 = 2448)
            partValue = (ordp*liveValues['Open'])/100
            ubl = liveValues['Open'] + partValue
            # LBL : #then LBL(Lower band limit)) is 2352 (2% of 2400, 2400 - 48 = 2352)
            lbl = liveValues['Open'] - partValue

        postions = models.Positions.objects.filter(instruments=acriptttt)
        potionObject = postions.values()[0]
        setQty = abs(potionObject['qty'])
        print('..........................setQty......... 1' , setQty)
        if -1<=setQty<=1:
            setQty = setQty
        else:
            setQty = int(setQty/2)
        print('..........................setQty......... 2' , setQty)

        if potionObject['positionType'] == "BUY":
            print(setQty,'SCRIPT QUANTITY=========================', 'BUY')
            views.tradeInitiateWithSLTG(type="SELL", scriptQty=setQty, exchangeType='NSE', sl=sl, tg=tg,
                                    ltp=liveValues['LTP'], scriptCode=acriptttt, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)
        if potionObject['positionType'] == "SELL":
            print(setQty,'SCRIPT QUANTITY=========================', 'SELL')
            views.tradeInitiateWithSLTG(type="BUY", scriptQty=setQty, exchangeType='NSE', sl=sl, tg=tg,
                                    ltp=liveValues['LTP'], scriptCode=acriptttt, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)

        response['error'] = 0
        response['status'] = "success"
        response["data"] = "stopSinglehalf_halfAlgo_manualAPI"
        return Response(response)
    except Exception as e:
        response['error'] = 1
        response['status'] = "error"
        response["data"] = str(e)
        return Response(response)

@api_view(["GET"])
def getPositions():
    """
        get live positions
    """
    positionsdict = kite.positions()
    #print(positionsdict)

    for pos in range(len(positionsdict['net'])):
        if (l_data := liveData.get(positionsdict['net'][pos]['tradingsymbol'])):
            pnl = (positionsdict['net'][pos]['sell_value']-positionsdict['net'][pos]['buy_value']) + (positionsdict['net'][pos]['multiplier']*l_data['LTP']*positionsdict['net'][pos]['quantity'])
            positionsdict['net'][pos]['pnl']=round(float(pnl),2)
            #positionsdict['net'][pos]['pnl']="+{}".format(round(float(pnl),2)) if float(pnl) > 0 else round(float(pnl),2) 

            if positionsdict['net'][pos]['quantity'] != 0 :             # used for % profit 
                    positionsdict['net'][pos]['last_price']  = ( positionsdict['net'][pos]['pnl'] / (positionsdict['net'][pos]['average_price']*0.20*positionsdict['net'][pos]['quantity']) )*100 
            else :
                if positionsdict['net'][pos]['buy_quantity'] != 0 :
                    positionsdict['net'][pos]['last_price']  = ((( positionsdict['net'][pos]['day_sell_price'] - positionsdict['net'][pos]['day_buy_price'])/positionsdict['net'][pos]['day_buy_quantity'] )*100*5)/ ( positionsdict['net'][pos]['day_buy_price']/positionsdict['net'][pos]['day_buy_quantity'] )

            if positionsdict['net'][pos]['quantity']==0 :
                positionsdict['net'][pos]['average_price']= positionsdict['net'][pos]['pnl']
            else:
                positionsdict['net'][pos]['average_price']=  positionsdict['net'][pos]['pnl']/positionsdict['net'][pos]['quantity']

            if positionsdict['net'][pos]['quantity']< 0 :
                if positionsdict['net'][pos]['pnl'] < 0 :
                    positionsdict['net'][pos]['average_price'] = 0 - positionsdict['net'][pos]['average_price'] 
          

                
    #print(positionsdict)
    consumers.updatePostions(positionsdict)
    positions = positionsdict['net']
    entryPrice = 0.0

    # print(positions)  #"+{}".format(round(float(pnl),2)) if float(pnl) > 0 else round(float(pnl),2)
    if len(positions) > 0:
        # if position is open in zerodha then update openPostion,startAlgo,exchangeType, isBuyClicked, isSellClicked, qty (check buy_quantity and sell_quantity value if both same then position is closed and if anyone is more than 0 then consider that postion is open)
        for position in positions:

            pnl = position['pnl']

            # For Open Buy position
            if int(position['quantity']) > 0:
                # print("Checking for buy postion " + position['tradingsymbol'])

                if models.ManualWatchlist.objects.filter(instruments=position['tradingsymbol']):
                    models.ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                        openPostion=True, startAlgo=True, positionType="BUY", isBuyClicked=False, isSellClicked=False)  # qty=position['quantity']
                    entryPrice = float(models.ManualWatchlist.objects.filter(
                        instruments=position['tradingsymbol']).values()[0]["entryprice"])
                elif models.AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']):
                    models.AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                        openPostion=True, startAlgo=True)
                    entryPrice = float(models.AlgoWatchlist.objects.filter(
                        instruments=position['tradingsymbol']).values()[0]["entryprice"])

                if not position_exists(position['tradingsymbol']):
                    # Calcualte SL and TG price for open postion and set regarding parameter for front update in Postion table
                    positionObject = models.Positions(instruments=position['tradingsymbol'], qty=position['quantity'], avgTradedPrice=round(
                        position['average_price'], 2), pnl=round(pnl, 3), startAlgo=True)
                    positionObject.save()
                    views.getPositionAndUpdateModels(
                        ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="BUY")
                else:
                    # print("Updating New Buy Positions")
                    views.getPositionAndUpdateModels(
                        ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="BUY")
                    models.Positions.objects.filter(instruments=position['tradingsymbol']).update(qty=position['quantity'], avgTradedPrice=round(
                        position['average_price'], 2), pnl=round(pnl, 3), startAlgo=True)

            # For Open sell position
            if int(position['quantity']) < 0:
                # print("Checking for Sell postion " + position['tradingsymbol'])
                setQty = abs(position['quantity'])

                if models.ManualWatchlist.objects.filter(instruments=position['tradingsymbol']):
                    models.ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                        openPostion=True, startAlgo=True, positionType="SELL", isBuyClicked=False, isSellClicked=False)  # , qty=setQty
                    entryPrice = float(models.ManualWatchlist.objects.filter(
                        instruments=position['tradingsymbol']).values()[0]["entryprice"])
                elif models.AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']):
                    models.AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                        openPostion=True, startAlgo=True)
                    entryPrice = float(models.AlgoWatchlist.objects.filter(
                        instruments=position['tradingsymbol']).values()[0]["entryprice"])

                if not position_exists(position['tradingsymbol']):
                    # Calcualte SL and TG price for open postion and set regarding parameter for front update in Postion table
                    positionObject = models.Positions(instruments=position['tradingsymbol'], qty=position['quantity'], avgTradedPrice=round(
                        position['average_price'], 2), pnl=round(pnl, 3), startAlgo=True)
                    positionObject.save()
                    views.getPositionAndUpdateModels(
                        ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="SELL")
                else:
                    # print("Updating New Sell Positions")
                    views.getPositionAndUpdateModels(
                        ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="SELL")
                    models.Positions.objects.filter(instruments=position['tradingsymbol']).update(qty=position['quantity'], avgTradedPrice=round(
                        position['average_price'], 2), pnl=round(float(pnl), 3), startAlgo=True)

            # For Closed Positions
            if int(position['quantity']) == 0:
                models.ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                    openPostion=False, startAlgo=False, positionType="", isBuyClicked=False, isSellClicked=False)
                models.AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                    openPostion=False, startAlgo=False)
                # print("Checking for closed postion " + position['tradingsymbol'])
                if not position_exists(position['tradingsymbol']):
                    print(pnl,'not posi')
                    positionObject = models.Positions(instruments=position['tradingsymbol'], qty=position['quantity'], entryprice=0.0, avgTradedPrice=round(position['average_price'], 2), lastTradedPrice=round(
                        position['last_price'], 2), pnl=pnl, unrealised=position['unrealised'], realised=position['realised'], startAlgo=False)
                    positionObject.save()
                else:
                    print("Updating New Positions",pnl)
                    models.Positions.objects.filter(instruments=position['tradingsymbol']).update(qty=position['quantity'], avgTradedPrice=round(position['average_price'], 2), lastTradedPrice=round(
                        position['last_price'], 2), pnl=pnl, unrealised=position['unrealised'], realised=position['realised'], startAlgo=False)
    # else:
    #     print("No postion available")


    positions_query =  models.Positions.objects.all()
    data = serializers.PositionsSerializer(positions_query, many=True).data
    return Response(data)


# Error


