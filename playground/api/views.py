from rest_framework.decorators import api_view
from rest_framework.response import Response  
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.views import APIView
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
from .permissions import CustomPermission
from rest_framework.permissions import AllowAny

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
        return Response({'Data':"User Authenticated"})    
    else:
        return Response({"Data": "User not Authenticated..Please log in "})
    
@api_view(["POST"])   
def logoutUser(request):
    logging.warning('Logout called = %s', kite.access_token)
    kite.invalidate_access_token()
    return Response({'Data':"User UnAuthenticated, please log back in.."})     


@api_view(["GET"])
def login_check_view(request):   
    if kite.access_token: 
        return Response({'Data':"User Authenticated"})    
    else:
        return Response({"Data": "User not Authenticated..Please log in "})


       
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
        return Response({"Data": "User not Authenticated..Please log in "})
    positionArray = views.getPositions()
    positionData = serializers.PositionsSerializer(positionArray, many=True).data
    totalPNL = views.total_pnl() or 0
    algoWatchlistArray = models.AlgoWatchlist.objects.all()
    algoData = serializers.AlgoWatchlistSerializer(algoWatchlistArray, many=True).data
    # allInstruments = list(models.Instruments.objects.all(
    # ).values_list('tradingsymbol', flat=True))
    return Response({'algoWatchlistArray': algoData, 'positionArray': positionData, 'totalPNL': totalPNL})

@api_view(["GET"])
def manualwatch(request):
    if kite.access_token is None:
        return Response({"Data": "User not Authenticated..Please log in "})
    positionArray = views.getPositions()
    totalPNL = views.total_pnl()
    manualWatchlistArray = models.ManualWatchlist.objects.all()
    # allInstruments = list(models.Instruments.objects.all(
    # ).values_list('tradingsymbol', flat=True))
    return Response({'manualWatchlistArray': manualWatchlistArray, 'positionArray': positionArray, 'totalPNL': totalPNL})

@api_view(['GET'])
def OrdersApi(reqeust):
    orders_qs = models.Orders.objects.all()
    order_json = serializers.OrderSerializer(orders_qs,many=True).data
    return Response(order_json)


class SettingsView(RetrieveUpdateAPIView):
    serializer_class = serializers.PreferencesSerializer
    queryset = models.Preferences.objects.first()
    permission_classes = [CustomPermission, AllowAny]
    
    # if kite.access_token is None:
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
       positions_qs = models.Positions.objects.all()
       positions_json = serializers.PositionsSerializer(positions_qs,many=True).data
       return Response(positions_json)


# Directly called by frontend to start process
class StartAlgoSingleAPI(APIView):
    """ Send Intrument name (TCS) and quantity in the parameter POST 
    {
        "instrument":"TCS",
        "instrumentQuantity":1
    }
    
    """
    def post(self,request):
        response = {'error':0,'status':''}
        try:            
            instruments_name = request.POST.get("instrument")   
            instruments_quantity = request.POST.get("instrumentQuantity")    
            # print("Came from JS to start" + params['instruments'])            
            models.AlgoWatchlist.objects.filter(instruments=instruments_name).update(startAlgo=True)
            models.AlgoWatchlist.objects.filter(instruments=instruments_name).update(qty=instruments_quantity)        
            response['status'] = 'success'
            return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = str(e)
            return Response(response)


class StopAlgoAndManualSingleAPI(APIView):
    """ Send Intrument name (TCS) ,quantity and is_algo in the parameter POST 
    {
        "instrument":"TCS",
        "instrumentQuantity":1,
        "is_algo": true // means manual instrument will be automaticly set to false
    }
    
    """
    def post(self,request):
        response = {'error':0,'status':''}
        try:
            instruments_name = request.POST.get("instrument")   
            instruments_quantity = request.POST.get("instrumentQuantity") 
            is_algo = request.POST.get("is_algo") 
            
            if is_algo == True or is_algo == "true" or is_algo == 1:
                print("Stop Single from Algowatchlist")
                models.AlgoWatchlist.objects.filter(
                    instruments=instruments_name).update(startAlgo=False)
                models.AlgoWatchlist.objects.filter(instruments=instruments_name).update(
                    qty=instruments_quantity)
            else:
                print("Stop Single from Manualwatchlist")
                models.ManualWatchlist.objects.filter(
                    instruments=instruments_name).update(startAlgo=False)
                models.ManualWatchlist.objects.filter(
                    instruments=instruments_name).update(isSellClicked=False)
                models.ManualWatchlist.objects.filter(
                    instruments=instruments_name).update(isBuyClicked=False)
                models.ManualWatchlist.objects.filter(instruments=instruments_name).update(
                    qty=instruments_quantity)
                       
            response['status'] = 'success'
            return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = str(e)
            return Response(response)

class StartAllAPI(APIView):
    """ Send Inothing in the POST request
    """
    def post(self,request):
        response = {'error':0,'status':''}
        try:
            instruments_quantity = request.POST.get("instrumentQuantity") 
            print("Came from JS to start All")
            algo_array = models.AlgoWatchlist.objects.all()
            print(len(algo_array))
            for items in algo_array:
                print("Starting for all items: ", items.instruments)
                models.AlgoWatchlist.objects.filter(instruments=items.instruments).update(startAlgo=True)
                models.AlgoWatchlist.objects.filter(instruments=items.instruments).update(qty=instruments_quantity)
            response['status'] = 'success'
            return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = str(e)
            return Response(response)

class BuySingleManualAPI(APIView):
    """ Send Intrument name (TCS) and quantity  in the parameter POST 
    {
        "instrument":"TCS",
        "instrumentQuantity":1,
    }
    
    """
    def post(self,request):
        response = {'error':0,'status':''}
        try:
            instruments_name = request.POST.get("instrument")   
            instruments_quantity = request.POST.get("instrumentQuantity") 
            
            models.ManualWatchlist.objects.filter(instruments=instruments_name).update(startAlgo=True)
            models.ManualWatchlist.objects.filter(instruments=instruments_name).update(positionType="BUY")
            models.ManualWatchlist.objects.filter(instruments=instruments_name).update(qty=instruments_quantity)
            models.ManualWatchlist.objects.filter(instruments=instruments_name).update(isBuyClicked=True)            
            response['status'] = 'success'
            return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = str(e)
            return Response(response)
        
        
class SellSingle(APIView):
    """ Send Intrument name (TCS) and quantity  in the parameter POST 
    {
        "instrument":"TCS",
        "instrumentQuantity":1,
    }
    
    """
    def post(self,request):
        response = {'error':0,'status':''}
        try:         
            instruments_name = request.POST.get("instrument")   
            instruments_quantity = request.POST.get("instrumentQuantity") 

            models.ManualWatchlist.objects.filter(instruments=instruments_name).update(startAlgo=True)
            models.ManualWatchlist.objects.filter(instruments=instruments_name).update(positionType="SELL")
            models.ManualWatchlist.objects.filter(instruments=instruments_name).update(qty=instruments_quantity)
            models.ManualWatchlist.objects.filter(instruments=instruments_name).update(isSellClicked=True)            
            response['status'] = 'success'
            return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = str(e)
            return Response(response)
       
       
        
class ScaleUpQtyAPI(APIView):
    """ Send Intrument name (TCS) ,quantity and is_algo in the parameter POST 
    {
        "instrument":"TCS",
        "instrumentQuantity":1,
        "is_algo": true // means manual instrument will be automaticly set to false
    }
    
    """
    def post(self,request):
        response = {'error':0,'status':''}
        try:
            instruments_name = request.POST.get("instrument")   
            instruments_quantity = request.POST.get("instrumentQuantity") 
            is_algo = request.POST.get("is_algo") 
            print("Updated QTY ===========+++++++", instruments_name, instruments_quantity, is_algo)
            if is_algo == True or is_algo == "true" or is_algo == 1:
                models.AlgoWatchlist.objects.filter(instruments=instruments_name).update(qty=instruments_quantity)
            else:
                models.ManualWatchlist.objects.filter(instruments=instruments_name).update(qty=instruments_quantity)                
            response['status'] = 'success'
            return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = str(e)
            return Response(response)

class ScaleDownQtyAPI(APIView):
    """ Send Intrument name (TCS) and quantity  in the parameter POST 
    {
        "instrument":"TCS",
        "instrumentQuantity":1,
    }
    
    """
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
            response['status'] = 'success'
            return Response(response)
        except Exception as e:
            response['error'] = 1
            response['status'] = str(e)
            return Response(response)

## Ahithi baki 6e API banavva ni
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
                return Response(response)                    
            elif flag == "AlgoWatch":
                instrumentObjectToAlgoWatchlistObject(instrumentObject)
                algoWatchObject = models.AlgoWatchlist.objects.filter(instruments=script).values()
                response = {'error':0,'status':'success','instrument':list(algoWatchObject)}
                return Response(response)                   
        except Exception as e:
            response = {'error':0,'status':str(e)}
            return Response(response)
            
class DeleteInstrumentAPI(APIView):
    """
    Will Delete the instruments
    """
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
            return Response(response)            
        except Exception as e:
            response = {'error':0,'status':str(e)}
            return Response(response)


def position_exists(tradingsymbol):
    return models.Positions.objects.filter(instruments=tradingsymbol).exists()


# @api_view(["GET"])
# def getPositions():
#     """
#         get live positions
#     """
#     positionsdict = kite.positions()
#     consumers.updatePostions(positionsdict)
#     positions = positionsdict['net']
#     entryPrice = 0.0

#     # print(positions)
#     if len(positions) > 0:
#         # if position is open in zerodha then update openPostion,startAlgo,exchangeType, isBuyClicked, isSellClicked, qty (check buy_quantity and sell_quantity value if both same then position is closed and if anyone is more than 0 then consider that postion is open)
#         for position in positions:
#             # print("Checking postion for " + position['tradingsymbol'])
#             if (l_data := consumers.liveData.get(position['tradingsymbol'])):
#                 pnl = (position['sell_value'] - position['buy_value']) + \
#                     (position['quantity'] * l_data['LTP']
#                      * position['multiplier'])
#             else:
#                 pnl = position['pnl']

#             # For Open Buy position
#             if int(position['quantity']) > 0:
#                 # print("Checking for buy postion " + position['tradingsymbol'])

#                 if models.ManualWatchlist.objects.filter(instruments=position['tradingsymbol']):
#                     models.ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
#                         openPostion=True, startAlgo=True, positionType="BUY", isBuyClicked=False, isSellClicked=False)  # qty=position['quantity']
#                     entryPrice = float(models.ManualWatchlist.objects.filter(
#                         instruments=position['tradingsymbol']).values()[0]["entryprice"])
#                 elif models.AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']):
#                     models.AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
#                         openPostion=True, startAlgo=True)
#                     entryPrice = float(models.AlgoWatchlist.objects.filter(
#                         instruments=position['tradingsymbol']).values()[0]["entryprice"])

#                 if not position_exists(position['tradingsymbol']):
#                     # Calcualte SL and TG price for open postion and set regarding parameter for front update in Postion table
#                     positionObject = models.Positions(instruments=position['tradingsymbol'], qty=position['quantity'], avgTradedPrice=round(
#                         position['average_price'], 2), pnl=round(pnl, 3), startAlgo=True)
#                     positionObject.save()
#                     views.getPositionAndUpdateModels(
#                         ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="BUY")
#                 else:
#                     # print("Updating New Buy Positions")
#                     views.getPositionAndUpdateModels(
#                         ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="BUY")
#                     models.Positions.objects.filter(instruments=position['tradingsymbol']).update(qty=position['quantity'], avgTradedPrice=round(
#                         position['average_price'], 2), pnl=round(pnl, 3), startAlgo=True)

#             # For Open sell position
#             if int(position['quantity']) < 0:
#                 # print("Checking for Sell postion " + position['tradingsymbol'])
#                 setQty = abs(position['quantity'])

#                 if models.ManualWatchlist.objects.filter(instruments=position['tradingsymbol']):
#                     models.ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
#                         openPostion=True, startAlgo=True, positionType="SELL", isBuyClicked=False, isSellClicked=False)  # , qty=setQty
#                     entryPrice = float(models.ManualWatchlist.objects.filter(
#                         instruments=position['tradingsymbol']).values()[0]["entryprice"])
#                 elif models.AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']):
#                     models.AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
#                         openPostion=True, startAlgo=True)
#                     entryPrice = float(models.AlgoWatchlist.objects.filter(
#                         instruments=position['tradingsymbol']).values()[0]["entryprice"])

#                 if not position_exists(position['tradingsymbol']):
#                     # Calcualte SL and TG price for open postion and set regarding parameter for front update in Postion table
#                     positionObject = models.Positions(instruments=position['tradingsymbol'], qty=position['quantity'], avgTradedPrice=round(
#                         position['average_price'], 2), pnl=round(pnl, 3), startAlgo=True)
#                     positionObject.save()
#                     views.getPositionAndUpdateModels(
#                         ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="SELL")
#                 else:
#                     # print("Updating New Sell Positions")
#                    views.getPositionAndUpdateModels(
#                          ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="SELL")
#                     models.Positions.objects.filter(instruments=position['tradingsymbol']).update(qty=position['quantity'], avgTradedPrice=round(
#                         position['average_price'], 2), pnl=round(pnl, 3), startAlgo=True)

#             # For Closed Positions
#             if int(position['quantity']) == 0:
#                 models.ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
#                     openPostion=False, startAlgo=False, positionType="", isBuyClicked=False, isSellClicked=False)
#                 models.AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
#                     openPostion=False, startAlgo=False)
#                 # print("Checking for closed postion " + position['tradingsymbol'])
#                 if not position_exists(position['tradingsymbol']):
#                     positionObject = models.Positions(instruments=position['tradingsymbol'], qty=position['quantity'], entryprice=0.0, avgTradedPrice=round(position['average_price'], 2), lastTradedPrice=round(
#                         position['last_price'], 2), pnl=round(pnl, 3), unrealised=position['unrealised'], realised=position['realised'], startAlgo=False)
#                     positionObject.save()
#                 else:
#                     # print("Updating New Positions")
#                     models.Positions.objects.filter(instruments=position['tradingsymbol']).update(qty=position['quantity'], avgTradedPrice=round(position['average_price'], 2), lastTradedPrice=round(
#                         position['last_price'], 2), pnl=round(pnl, 3), unrealised=position['unrealised'], realised=position['realised'], startAlgo=False)
#     # else:
#     #     print("No postion available")

#     positions_query =  models.Positions.objects.all()
#     data = serializers.PositionsSerializer(positions_query, many=True).data
#     return Response(data)


## Error


