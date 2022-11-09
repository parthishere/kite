from dis import Instruction
import imp, array
import logging
from multiprocessing import context
from pickle import FALSE, TRUE
from urllib import response
from django.shortcuts import render, redirect
from django.http import HttpResponse
from playground import kiteconnect, constants
from playground.models import Preferences, Instruments, AlgoWatchlist, ManualWatchlist, Positions, Orders
from django.contrib import messages
from kiteconnect import KiteConnect, KiteTicker
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from json import dumps
from django.db.models import Q
from django.db.models import Sum
import datetime, time
import js2py

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key=constants.KITE_API_KEY)

algoWatchlistArray = []
manualWatchlistArray = []
instrumentArray = []
positionArray = []
ordersArray = []
subscriberlist = {}
liveData = {}
byPassZerodha = True

#Variable Required for logic implementation
algoWatchlistEnable = False
SLPrice = 0.0
TGPrice = 0.0

#=========================
## All Views Functions
#=========================
def index(request):
    return render(request, 'index.html')    

def home(request):
    return render(request, 'home.html')

def loginUser(request):
    if request.method == 'GET':
        if request.GET['request_token'] != "":
            data = kite.generate_session(request.GET['request_token'], api_secret=constants.KITE_API_SECRETE)
            kite.set_access_token(data["access_token"])
            clearAllData()
            # startLiveConnection(str(kite.access_token))
            getPositions()
            # return render(request, 'algowatch.html')
            return render(request, 'home.html')
        messages.error(request, 'Authentication Failed! Please login again')

def algowatch(request):

    #Return to home page is user is not loggedin using Zerodha
    if kite.access_token is None and byPassZerodha:
        messages.error(request, 'Authentication Failed! Please login again')
        return redirect("/")
    
    #Clear all the model data if required
    # clearAllData()

    #If user is loggedin using Zerodha then fetch instrument list from the Zerodha using kite api.
    # refreshIntruments()

    # instrumentUpdate = Instruments.objects.filter(instrument_token="140033")
    # print(instrumentUpdate.values()[0]['tradingsymbol'])
    instrumentUpdate = Instruments.objects.filter(Q(tradingsymbol='ITC', exchange = 'NSE') | Q(tradingsymbol='HDFC', exchange = 'NSE') |  Q(tradingsymbol='RELIANCE', exchange = 'NSE') | Q(tradingsymbol='BPCL', exchange = 'NSE') | Q(tradingsymbol='ABB', exchange = 'NSE') | Q(tradingsymbol='IEX', exchange = 'NSE')).values()
    instrumentObjectToAlgoWatchlistObject(instrumentUpdate)
    algoWatchlistArray = AlgoWatchlist.objects.all()
    positionArray = getPositions()
    totalPNL = total_pnl()
    for tokens in algoWatchlistArray:
        if not tokens.instrumentsToken in subscriberlist:
            subscriberlist[int(tokens.instrumentsToken)] = tokens.instruments
    # print(subscriberlist)

    return render(request, 'algowatch.html', {'algoWatchlistArray': algoWatchlistArray, 'positionArray': positionArray, 'totalPNL' : totalPNL})
    
def manualwatch(request):

    if kite.access_token is None and byPassZerodha:
        return redirect("/")
    
    instrumentUpdate = Instruments.objects.filter(Q(tradingsymbol='CIPLA', exchange = 'NSE') | Q(tradingsymbol='TATASTEEL', exchange = 'NSE') |  Q(tradingsymbol='TITAN', exchange = 'NSE') | Q(tradingsymbol='TECHM', exchange = 'NSE') | Q(tradingsymbol='ACC', exchange = 'NSE')).values()
    instrumentObjectToManualWatchlistObject(instrumentUpdate)
    manualWatchlistArray = ManualWatchlist.objects.all()
    positionArray = getPositions()
    totalPNL = total_pnl()
    return render(request, 'manualwatch.html', {'manualWatchlistArray': manualWatchlistArray, 'positionArray': positionArray, 'totalPNL' : totalPNL})

def orders(request):

    if kite.access_token is None and byPassZerodha:
        return redirect("/")

    ordersArray = getOrders()
    # print(orderArray)
    # print(orderArray.values().count())
    # print(ordersArray.values()[1]['orderId'])
    return render(request, 'orders.html', {'orderArrayList': ordersArray})

def settings(request):
    if kite.access_token is None and byPassZerodha:
        return redirect("/")

    if request.method == "POST":
        time = request.POST.get('time')
        stoploss = request.POST.get('stoploss')
        target = request.POST.get('target')
        scaleupqty = request.POST.get('scaleupqty')
        scaledownqty = request.POST.get('scaledownqty')
        openingrange = request.POST.get('openingrange')
        openingrangebox = request.POST.get('openingrangebox')
        settings = Preferences(time=time, stoploss=stoploss, target=target, scaleupqty=scaleupqty, scaledownqty=scaledownqty, openingrange=openingrange)
        settings.save()
        messages.success(request, 'Preference updated successfully!')
    return render(request, 'settings.html', {'name': 'Settings'})

def logoutUser(request):
    kite.invalidate_access_token()
    return redirect("/")

#=========================
## All Supported Functions
#=========================
def clearAllData():
    AlgoWatchlist.objects.all().delete()
    ManualWatchlist.objects.all().delete()
    Positions.objects.all().delete()
    Orders.objects.all().delete()

#Refresh this instrument only once in a day at 8:30AM first login.
#Update trading symbol if it is already exist in the database and insert it if it is not available
def refreshIntruments():

    for item in kite.instruments():
        instrument_token = item["instrument_token"]
        exchange_token = item["exchange_token"]
        tradingsymbol = item["tradingsymbol"]
        name = item["name"]
        expiry = item["expiry"]
        tick_size = item["tick_size"]
        strike = item["strike"]
        lot_size = item["lot_size"]
        instrument_type = item["instrument_type"]
        segment = item["segment"]
        exchange = item["exchange"]

    if instrument_exists(tradingsymbol):
        instrumentUpdate = Instruments.objects.get(tradingsymbol=tradingsymbol)
        instrumentUpdate.instrument_token = instrument_token
        instrumentUpdate.exchange_token = exchange_token
        instrumentUpdate.tradingsymbol = tradingsymbol
        instrumentUpdate.name = name
        instrumentUpdate.expiry = expiry
        instrumentUpdate.tick_size = tick_size
        instrumentUpdate.strike = strike
        instrumentUpdate.lot_size = lot_size
        instrumentUpdate.instrument_type = instrument_type
        instrumentUpdate.segment = segment
        instrumentUpdate.exchange = exchange
        instrumentUpdate.save()
    else:
        instrumentModel = Instruments(instrument_token=instrument_token, exchange_token=exchange_token, tradingsymbol=tradingsymbol,name=name,expiry=expiry,tick_size=tick_size,strike=strike,lot_size=lot_size,instrument_type=instrument_type,segment=segment,exchange=exchange)
        instrumentModel.save()

def instrumentObjectToManualWatchlistObject(instrumentUpdate):
    for instrumentObject in instrumentUpdate:
        tradingSymbol = instrumentObject.get('tradingsymbol')
        if not ManualWatchlist.objects.filter(instruments=tradingSymbol).exists():
            manualWatlistObject = ManualWatchlist(instruments=tradingSymbol, instrumentsToken = instrumentObject.get('instrument_token'))
            manualWatlistObject.save()
    
def instrumentObjectToAlgoWatchlistObject(instrumentUpdate):
    for instrumentObject in instrumentUpdate:
        tradingSymbol = instrumentObject.get('tradingsymbol')
        if not AlgoWatchlist.objects.filter(instruments=tradingSymbol).exists():
            algoWatlistObject = AlgoWatchlist(instruments=tradingSymbol, instrumentsToken = instrumentObject.get('instrument_token'))
            algoWatlistObject.save()
            
def username_exists(username):
    return User.objects.filter(username=username).exists()

def instrument_exists(tradingsymbol):
    return Instruments.objects.filter(tradingsymbol=tradingsymbol).exists()

def position_exists(tradingsymbol):
    return Positions.objects.filter(instruments=tradingsymbol).exists()

def order_exists(orderId):
    return Orders.objects.filter(orderId=orderId).exists()

def getPositions():
    positionsdict = kite.positions()
    # print(positionsdict['net'])
    positions = positionsdict['net']
    for position in positions:
        if not position_exists(position['tradingsymbol']):
            positionObject = Positions(instruments = position['tradingsymbol'], qty = position['quantity'], entryprice = 0.0, avgTradedPrice = position['average_price'], lastTradedPrice = position['last_price'], pnl = position['pnl'], unrealised = position['unrealised'], realised = position['realised'])
            positionObject.save()
    return Positions.objects.all()

def getOrders():
    orders = kite.orders()
    # print(ordersdict)
    # orders = ordersdict['data']
    
    for order in orders:
        if not order_exists(order['order_id']):
            orderObject = Orders(instruments = order['tradingsymbol'], qty = order['quantity'], 
                status = order['status'], avgTradedPrice = order['average_price'], instrumentsToken = order['instrument_token'], 
                orderTimestamp = order['order_timestamp'], orderType = order['order_type'], transactionType = order['transaction_type'],
                product=order['product'], orderId =order['order_id'] )
            orderObject.save()
    return Orders.objects.all()

def total_pnl():
    total = Positions.objects.aggregate(TOTAL = Sum('pnl'))['TOTAL']
    return total

#=========================
## Websocket Data Connection Methods
#=========================
def startLiveConnection(token):
    kws = KiteTicker(api_key=constants.KITE_API_KEY, access_token=token)
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.connect(threaded=True)

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    # logging.debug("Ticks: {}".format(ticks))
    for stock in ticks:
        liveData[subscriberlist[stock['instrument_token']]] = stock['last_price']
        print(liveData)

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    print(subscriberlist)
    ws.subscribe([3329, 134657, 340481, 56321, 424961, 738561])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_LTP, [3329, 134657, 340481, 56321, 424961, 738561])

def on_close(ws, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()

# kws.on_close = on_close

# while len(liveData.keys()) != len(list(subscriberlist.keys())):
#     continue

# print("Connected to web socket")

# while datetime.time(9,15,30) >= datetime.datetime.now().time():
#     time.sleep(2)

# #strategy loop
# history = {}
# while datetime.time(9,15,30) < datetime.datetime.now().time() < datetime.time(15,15):
#     for symbol, values in liveData.items():
#         try:
#             history[symbol]
#         except:
#             history[symbol] = {"Open": values["Open"], "Traded": False}
#         if values["last_price"] > values["Open"]:
#             print("Buy Place Order")
#         if values["last_price"] < history[symbol]["Open"]:
#             print("Place Sell Order")



#Steps for the logic
#1. Run a loog for all watchlist items 

    #Get value from Settings
    #TG : Get % value from settings
    #SL : Get % value from settings
    #TIME : Get seconds value from settings
    #OR : Get % value from settings and of difference from CMP to OPEN
    #ORD :  Get true of fale from Settings to apply ORD or not
    #UBL : #then UBL(Upper band limit)) is 2448 (2% of 2400, 2400 + 48 = 2448)
    #LBL : #then LBL(Lower band limit)) is 2352 (2% of 2400, 2400 - 48 = 2352)
    #SLHit: 0 #Counter for SL Hit for particualr script

    #====For Cash Segment======#
    #ScaleupHit: Base should be 0 and increment to 1,2,3,4 #Read the click of Scaleup button on algowatchlist, i.e 1
    #CalculateQTYForNextTrade = ScriptQTY*ScaleupHit (125*1 = 125), (125*2 = 250), (125*3 = 375)

    #ScaledownHit: It will basically divided the qty by 2 so it will reduce qty by double
    #CalculateQTYForNextTrade = ScriptQTY*ScaleupHit (125/2 = 62.5 but it will take decimal value which is 62)
    #====For FO Segment======#
    #ScaleupHit: Base should be 0 and increment to 1,2,3,4 #Read the click of Scaleup button on algowatchlist, i.e 1
    #Read FO Lot size and it will increase but its lot size (Reliance lot size is 250)
    #CalculateQTYForNextTrade = ScriptQTY*ScaleupHit (250*1 = 125), (250*2 = 250), (250*3 = 375)

    #ScaledownHit: It will basically divided the qty by 2 so it will reduce qty by double
    #CalculateQTYForNextTrade = ScriptQTY*ScaleupHit (250/2 = Not work as it is base lot size and not divisable further, but 
    # for 500, 500/2 = 250)
    #====For FO Segment======#

    #ScriptQTY: Read the QTY from watchlist i.e 125


    #Reliance
    #IF_Check if Algo is started and Not any positon open for that script
        #IF_ORD True
            #IF_check CMP > OPEN and (CMP > LBL and CMP > UPL)
                #tradeSetup()
                #Place BUY Order (with ScriptQTY)
                #Set SL variable
                #Set TG Variable
            #ELSE_#check CMP < OPEN and (CMP > LBL and CMP > UPL)
                #tradeSetup()   
                #Place SELL order (with ScriptQTY)
                #Set SL variable
                #Set TG Variable
        #ELSE_ORD False
            #IF_check CMP > OPEN
                #tradeSetup()
                #Place BUY Order (with ScriptQTY)
                #Set SL variable
                #Set TG Variable
            #ELSE_#check CMP < OPEN
                #tradeSetup()
                #Place SELL order (with ScriptQTY)
                #Set SL variable
                #Set TG Variable
    #ELSEIF_check if Algo is started and Position Open (Either Buy or Sell)
        #IF_check if position is BUY and 
            #if CMP <= SL
                #tradeSetup()
                #Place SELL order (with ScriptQTY)
                #Set SL variable
                #Set TG Variable
                #SLHit count ++
            #IF CMP >= TG
                #Close Postions and stop algo
        #ELSE_check if positino is SELL
            #if CMP >= SL
                #tradeSetup()
                #Place BUY order (with ScriptQTY)
                #Set SL variable
                #Set TG Variable
                #SLHit count ++
            #IF CMP <= TG
                #Close Postions and stop algo
    #ELSE_check if algo is stopped and Position Open (Either Buy or Sell)
        #Close postion for this script


#=========================
## Algo Commonn Methods
#=========================

def stopAll(request):
    print("Came from JS to stop All" + request.POST['text'])
    return HttpResponse(request.POST['text'])
    #Loop of array and close individuals if any position open
    algoWatchlistEnable = False

def startAll(request):
    print("Came from JS to start All" + request.POST['text'])
    return HttpResponse(request.POST['text'])
    #Start Algo for items in AlgoWatchlist
    algoWatchlistEnable = True

def startSingle(request): #For Manual watchlist
    print("Came from JS to start" + request.POST['text'])
    return HttpResponse(request.POST['text'])
    # tradeInitiateWithSLTG(type, scriptQty, scriptCode)

def buySingle(request): #For Manual watchlist
    print("Came from JS to buy single" + request.POST['text'])
    return HttpResponse(request.POST['text'])

def sellSingle(request): #For Manual watchlist
    print("Came from JS to sell single" + request.POST['text'])
    return HttpResponse(request.POST['text'])

def stopSingle(request): #For Manual and Algo watchlist
    print("Came from JS to stop" + request.POST['text'])
    return HttpResponse(request.POST['text'])
    # tradeClose(orderId=orderId)

def tradeInitiateWithSLTG(type, exchangeType, scriptQty, scriptCode, slprtg, tgprtg):
    #type should be "BUY" or "SELL"
    #exchangeType should be "NFO" or "NSE"
    print(type)
    print(exchangeType)
    print(scriptQty)
    print(scriptCode)
    print(slprtg)
    print(tgprtg)
    #Place order (with ScriptQTY)
    try:
        orderId = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchangeType, 
                    tradingsymbol=scriptCode, transaction_type=type, quantity=scriptQty,
                    product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_MARKET, validity=kite.VALIDITY_DAY)
        logging.info("Order placed. ID is: {}".format(orderId))
        messages.success("Order placement failed: {}".format(e.message))
        #Set SL variable
        #Set TG Variable
        if type == "BUY":
            SLPrice = 1.0 #Calculate from price that order placed and - slprtg
            TGPrice = 1.0 #Calculate from price that order placed and + tgprtg
        else:
            SLPrice = 1.0 #Calculate from price that order placed and + slprtg
            TGPrice = 1.0 #Calculate from price that order placed and - tgprtg
    except Exception as e:
        logging.info("Order placement failed: {}".format(e.message))
        messages.error("Order placement failed: {}".format(e.message))

def tradeClose(orderId):
    kite.exit_order(variety=kite.VARIETY_REGULAR, order_id=orderId)
