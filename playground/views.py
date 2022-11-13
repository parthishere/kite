from dis import Instruction
import imp, array
import logging
from multiprocessing import context
from pickle import FALSE, TRUE
from threading import Thread
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
import threading
from random import randint

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key=constants.KITE_API_KEY)

manualWatchlistArray = []
instrumentArray = []
positionArray = []
ordersArray = []
subscriberlist = {}
# liveData = {}
liveData = {'ABB': {'Open': 3103.9, 'High': 3240.0, 'Low': 3054.5, 'Close': 3103.9, 'LTP': 3166.9}, 'ITC': {'Open': 359.0, 'High': 359.9, 'Low': 354.1, 'Close': 360.7, 'LTP': 356.0}, 'BPCL': {'Open': 306.0, 'High': 307.95, 'Low': 304.2, 'Close': 306.85, 'LTP': 305.5}, 'HDFC': {'Open': 2480.2, 'High': 2508.4, 'Low': 2467.8, 'Close': 2503.5, 'LTP': 2504.1}, 'RELIANCE': {'Open': 2590.0, 'High': 2596.55, 'Low': 2563.0, 'Close': 2604.0, 'LTP': 2572.5}, 'IEX': {'Open': 142.6, 'High': 142.6, 'Low': 138.85, 'Close': 142.6, 'LTP': 140.2}}
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
    
    # daemon = Thread(target=refreshIntrumentList, daemon=True, name='Monitor')
    # daemon.start()
    # print('Waiting for the thread...')
    # daemon.join()
    return render(request, 'home.html')
    
def loginUser(request):
    if request.method == 'GET':
        if request.GET['request_token'] != "":
            data = kite.generate_session(request.GET['request_token'], api_secret=constants.KITE_API_SECRETE)
            kite.set_access_token(data["access_token"])
            # clearAllData()
            # startLiveConnection(str(kite.access_token))
            # return render(request, 'algowatch.html')
            threading.Timer(1.0, coreLogic(liveData)).start()
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
    # refreshIntrumentList()()

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
    return render(request, 'algowatch.html', {'algoWatchlistArray': algoWatchlistArray, 'positionArray': positionArray, 'totalPNL' : totalPNL})
    
def manualwatch(request):

    if kite.access_token is None and byPassZerodha:
        return redirect("/")
    
    instrumentUpdate = Instruments.objects.filter(Q(tradingsymbol='ITC', exchange = 'NSE') | Q(tradingsymbol='HDFC', exchange = 'NSE') |  Q(tradingsymbol='RELIANCE', exchange = 'NSE') | Q(tradingsymbol='BPCL', exchange = 'NSE') | Q(tradingsymbol='ABB', exchange = 'NSE') | Q(tradingsymbol='IEX', exchange = 'NSE')).values()
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
    # Instruments.objects.all().delete()
    AlgoWatchlist.objects.all().delete()
    ManualWatchlist.objects.all().delete()
    Positions.objects.all().delete()
    Orders.objects.all().delete()

#Refresh this instrument only once in a day at 8:30AM first login.
#Update trading symbol if it is already exist in the database and insert it if it is not available
def refreshIntrumentList():
    instrumentList = kite.instruments(exchange='NSE')
    for item in instrumentList:

        
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
            # print(item)
            # print("Updating instruments")
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
            # print(item)
            # print("Adding instruments")
            instrumentModel = Instruments(instrument_token=instrument_token, exchange_token=exchange_token, tradingsymbol=tradingsymbol,name=name,expiry=expiry,tick_size=tick_size,strike=strike,lot_size=lot_size,instrument_type=instrument_type,segment=segment,exchange=exchange)
            instrumentModel.save()

def instrumentObjectToManualWatchlistObject(instrumentUpdate):
    for instrumentObject in instrumentUpdate:
        tradingSymbol = instrumentObject.get('tradingsymbol')
        if not ManualWatchlist.objects.filter(instruments=tradingSymbol).exists():
            manualWatlistObject = ManualWatchlist(instruments=tradingSymbol, instrumentsToken = instrumentObject.get('instrument_token'),
            exchangeType = instrumentObject.get('exchange'), segment = instrumentObject.get('segment'), instrumentType = instrumentObject.get('instrument_type'))
            manualWatlistObject.save()
    
def instrumentObjectToAlgoWatchlistObject(instrumentUpdate):
    for instrumentObject in instrumentUpdate:
        tradingSymbol = instrumentObject.get('tradingsymbol')
        if not AlgoWatchlist.objects.filter(instruments=tradingSymbol).exists():
            algoWatlistObject = AlgoWatchlist(instruments=tradingSymbol, instrumentsToken = instrumentObject.get('instrument_token'),
            exchangeType = instrumentObject.get('exchange'), segment = instrumentObject.get('segment'), instrumentType = instrumentObject.get('instrument_type'))
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
        liveData[subscriberlist[stock['instrument_token']]] = {"Open": stock['ohlc']['open'],
            "Open": stock['ohlc']['open'],
            "High": stock['ohlc']['high'],
            "Low": stock['ohlc']['low'],
            "Close": stock['ohlc']['close'],
            "LTP": stock['last_price']}
        print("Checking live data")
        print(liveData)

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    print(subscriberlist)
    ws.subscribe([3329, 134657, 340481, 56321, 424961, 738561])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, [3329, 134657, 340481, 56321, 424961, 738561])

def on_close(ws, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()

# kws.on_close = on_close

#=========================
## Algo Core Logic Method
#=========================
#Steps for the logic
def coreLogic(liveData): #A methond to check 
    print("Run every second")
    watchForAlgowatchlistBuySellLogic(liveData)
    watchForManualListBuySellLogic(liveData)

def watchForAlgowatchlistBuySellLogic(liveData):
    algoArray = AlgoWatchlist.objects.all()
    #Get value from Settings
    settings = Preferences.objects.all()
    #TG : Get % value from settings
    tg = settings.values()[0]['target']
    #SL : Get % value from settings
    sl = settings.values()[0]['stoploss']
    #TIME : Get seconds value from settings
    startTime = settings.values()[0]['time']
    #OR : Get % value from settings and of difference from CMP to OPEN
    ordp = settings.values()[0]['openingrange']
    #ORD :  Get true of fale from Settings to apply ORD or not
    ordtick = settings.values()[0]['openingrangebox']

    # 1. Run a loog for all watchlist items 
    for items in algoArray: #Reliance

        liveValues = liveData[items.instruments]
        #UBL : #then UBL(Upper band limit)) is 2448 (2% of 2400, 2400 + 48 = 2448)
        partValue = (ordp*liveValues['Open'])/100
        ubl = liveValues['Open'] + partValue
        #LBL : #then LBL(Lower band limit)) is 2352 (2% of 2400, 2400 - 48 = 2352)
        lbl = liveValues['Open'] - partValue
        # #SLHit: 0 #Counter for SL Hit for particualr script
        print("Checking algo for " + items.instruments)
        if items.startAlgo and not items.openPostion: #IF_Check if Algo is started and Not any positon open for that script
            if ordtick: #IF_ORD True check if open is in range
                if (liveValues['LTP'] > liveValues['Open']) and (liveValues['LTP'] < ubl and liveValues['LTP'] > lbl): #IF_check CMP > OPEN and (CMP > LBL and CMP > UPL)
                    print("Opening range is selected so only checking both ltp > Open and ltp in in range")
                    tradeInitiateWithSLTG(type="BUY", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True)
                elif (liveValues['LTP'] < liveValues['Open']) and (liveValues['LTP'] < ubl and liveValues['LTP'] > lbl): #ELSE_#check CMP < OPEN and (CMP > LBL and CMP > UPL)
                    print("Opening range is selected so only checking both ltp < Open and ltp in in range")
                    tradeInitiateWithSLTG(type="SELL", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True)
            else: #ELSE_ORD False means do not check if open is in range 
                if liveValues['LTP'] > liveValues['Open']: #IF_check CMP > OPEN
                    print("Opening range is not selected so only checking ltp > Open")
                    tradeInitiateWithSLTG(type="BUY", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True)
                elif liveValues['LTP'] < liveValues['Open']: #ELSE_#check CMP < OPEN
                    print("Opening range is not selected so only checking ltp < Open")
                    tradeInitiateWithSLTG(type="SELL", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True)
                
        elif items.startAlgo and items.openPostion: #ELSEIF_check if Algo is started and Position Open (Either Buy or Sell)
            postions = Positions.objects.filter(instruments=items.instruments)
            if postions:
                potionObject = postions.values()[0]
                if potionObject['positionType'] == "BUY": #IF_check if position is BUY and 
                    if liveValues['LTP'] <= potionObject['slPrice']:
                        tradeInitiateWithSLTG(type="SELL", scriptQty=(items.qty)*2, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True)
                        items.slHitCount = items.slHitCount + 1
                    elif liveValues['LTP'] >= potionObject['tgPrice']: #IF CMP >= TG
                        tradeClose(orderId=potionObject['orderId'], isFromAlgo=True) #Close Postions and stop algo
                    else:
                        print("Position BUYALGO, No SL, No TG so continue")
                elif potionObject['positionType'] == "SELL":#ELSE_check if positino is SELL
                    if liveValues['LTP'] >= potionObject['slPrice']: #if CMP >= SL
                        tradeInitiateWithSLTG(type="BUY", scriptQty=(items.qty)*2, exchangeType=items.exchangeType, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True)
                        items.slHitCount = items.slHitCount + 1 #SLHit count ++
                    elif liveValues['LTP'] <= potionObject['tgPrice']: #IF CMP <= TG
                        tradeClose(orderId=potionObject['orderId'], isFromAlgo=True) #Close Postions and stop algo
                    else:
                        print("Position SELLALGO, No SL, No TG so continue")
        elif not items.startAlgo and items.openPostion: #ELSE_check if algo is stopped and Position Open (Either Buy or Sell)
            postions = Positions.objects.filter(instruments=items.instruments)
            print("Algo stopped and closing trade")
            print(postions)
            AlgoWatchlist.objects.filter(instruments = items.instruments).update(openPostion = False)
            tradeClose(orderId=postions.values()[0]['orderid'], isFromAlgo=True) #Close postion for this script
        else:
            print("Nothing to trade from Algo Watchlist for " + items.instruments) 
    print("No script found to trade")

def watchForManualListBuySellLogic(liveData):
    manualArray = ManualWatchlist.objects.all()
    settings = Preferences.objects.all()
    #TG : Get % value from settings
    tg = settings.values()[0]['target']
    #SL : Get % value from settings
    sl = settings.values()[0]['stoploss']
    buyClicked = True
    sellClicked = False

    for items in manualArray: #Reliance

        print("Checking manual for " + items.instruments)
        liveValues = liveData[items.instruments]
        if items.startAlgo and not items.openPostion:
            if items.isBuyClicked: #IF_Buy_Clicked then Place buy order no condition need to check
                print("Buying Manually")
                tradeInitiateWithSLTG(type="BUY", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False)
            elif items.isSellClicked:
                print("Selling Manually")
                tradeInitiateWithSLTG(type="SELL", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False) 
            else:
                print("Nothing to trade from Manual Watchlist")
        elif items.startAlgo and items.openPostion:

            print("Algo is running and postion is also running so checking for SL or TG")
            postions = Positions.objects.filter(instruments=items.instruments)
            if postions:
                potionObject = postions.values()[0]
                if potionObject['positionType'] == "BUY": #IF_check if position is BUY and 
                    if liveValues['LTP'] <= potionObject['slPrice']:
                        tradeInitiateWithSLTG(type="SELL", scriptQty=(items.qty)*2, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False)
                        items.slHitCount = items.slHitCount + 1
                    elif liveValues['LTP'] >= potionObject['tgPrice']: #IF CMP >= TG
                        tradeClose(orderId=potionObject['orderId'], isFromAlgo=False, scriptCode=items.instruments) #Close Postions and stop algo
                    else:
                        print("Position BUYMANUAL, No SL, No TG so continue")
                elif potionObject['positionType'] == "SELL":#ELSE_check if positino is SELL
                    if liveValues['LTP'] >= potionObject['slPrice']: #if CMP >= SL
                        tradeInitiateWithSLTG(type="BUY", scriptQty=(items.qty)*2, exchangeType=items.exchangeType, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False)
                        items.slHitCount = items.slHitCount + 1 #SLHit count ++
                    elif liveValues['LTP'] <= potionObject['tgPrice']: #IF CMP <= TG
                        tradeClose(orderId=potionObject['orderId'], isFromAlgo=False, scriptCode=items.instruments) #Close Postions and stop algo
                    else:
                        print("Position SELLMANUAL, No SL, No TG so continue")
        elif not items.startAlgo and items.openPostion:
            print("Algo is stopped and postion is running so closing the trade")
            postions = Positions.objects.filter(instruments=items.instruments)
            if postions:
                potionObject = postions.values()[0]
                tradeClose(orderId=potionObject['orderId'], isFromAlgo=False, scriptCode=items.instruments) #Close Postions and stop algo
        else:
            print("Nothing to trade in Manual Watchlist")
        


#=========================
## Algo Commonn Methods
#=========================

def stopAll(request):
    print("Came from JS to stop All")
    algoArray = AlgoWatchlist.objects.all()
    for items in algoArray:
        AlgoWatchlist.objects.filter(instruments = items.instruments).update(startAlgo = True)
        AlgoWatchlist.objects.filter(instruments = items.instruments).update(qty = int(request.POST['scriptQty']))
    coreLogic(liveData)
    return HttpResponse()

def startAll(request):
    print("Came from JS to start All")
    algoArray = AlgoWatchlist.objects.all()
    for items in algoArray:
        AlgoWatchlist.objects.filter(instruments = items.instruments).update(startAlgo = False)
        AlgoWatchlist.objects.filter(instruments = items.instruments).update(qty = int(request.POST['scriptQty']))
    coreLogic(liveData)    
    return HttpResponse()

def startSingle(request): #For Manual watchlist
    print("Came from JS to start" + request.POST['scriptQty'])
    AlgoWatchlist.objects.filter(instruments = request.POST['script']).update(startAlgo = True)
    AlgoWatchlist.objects.filter(instruments = request.POST['script']).update(qty = int(request.POST['scriptQty']))
    coreLogic(liveData)
    return HttpResponse(request.POST['script'])
    
    # tradeInitiateWithSLTG(type, scriptQty, scriptCode)

def buySingle(request): #For Manual watchlist
    print("Came from JS to buy single" + request.POST['script'])
    print("Came from JS to start" + request.POST['scriptQty'])
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(startAlgo = True)
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(qty = int(request.POST['scriptQty']))
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(isBuyClicked = True)
    coreLogic(liveData)
    return HttpResponse(request.POST['text'])

def sellSingle(request): #For Manual watchlist
    print("Came from JS to sell single" + request.POST['script'])
    print("Came from JS to start" + request.POST['scriptQty'])
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(startAlgo = True)
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(qty = int(request.POST['scriptQty']))
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(isSellClicked = True)
    coreLogic(liveData)
    return HttpResponse(request.POST['text'])

def stopSingle(request): #For Manual and Algo watchlist
    print("Came from JS to stop" + request.POST['script'])
    if request.POST['isFromAlgoTest'] == "true":
        print("Stop Single from Algowatchlist")
        AlgoWatchlist.objects.filter(instruments = request.POST['script']).update(startAlgo = False)
        AlgoWatchlist.objects.filter(instruments = request.POST['script']).update(qty = int(request.POST['scriptQty']))
    else: 
        print("Stop Single from Manualwatchlist")
        ManualWatchlist.objects.filter(instruments = request.POST['script']).update(startAlgo = False)
        ManualWatchlist.objects.filter(instruments = request.POST['script']).update(isSellClicked = False)
        ManualWatchlist.objects.filter(instruments = request.POST['script']).update(isBuyClicked = False)
    coreLogic(liveData)
    return HttpResponse(request.POST['script'])

def tradeInitiateWithSLTG(type, exchangeType, scriptQty, scriptCode, ltp, sl, tg, isFromAlgo):
    #type should be "BUY" or "SELL"
    #exchangeType should be "NFO" or "NSE"
    print(type)
    print(exchangeType)
    print(scriptQty)
    print(scriptCode)
    print(ltp)
    print(sl)
    print(tg)
    #Place order (with ScriptQTY)
    try:
        # orderId = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchangeType, 
        #             tradingsymbol=scriptCode, transaction_type=type, quantity=scriptQty,
        #             product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_MARKET, validity=kite.VALIDITY_DAY)
        # logging.info("Order placed. ID is: {}".format(orderId))
        # messages.success("Order placement failed: {}".format(e.message))
        
        #Set SL variable
        #Set TG Variable
        orderId = random_with_N_digits(4)
        if type == "BUY":
            partValueSL = (sl*ltp)/100
            partValueTG = (tg*ltp)/100
            slValue = ltp - partValueSL
            tgValue = ltp + partValueTG
            print("SL and TG setup after Buy")
            print(slValue)
            print(tgValue)
            if position_exists(scriptCode):
                Positions.objects.filter(instruments=scriptCode).update(slPrice=slValue, tgPrice=tgValue, entryprice=ltp, orderId=orderId, positionType="BUY")
            else:
                positionObject = Positions(instruments = scriptCode, qty = scriptQty, avgTradedPrice = ltp, lastTradedPrice = ltp,
                slPrice=slValue, tgPrice=tgValue, entryprice=ltp, orderId=orderId, positionType="BUY")
                positionObject.save()
        else:
            partValueSL = (sl*ltp)/100
            partValueTG = (tg*ltp)/100
            slValue = ltp + partValueSL
            tgValue = ltp - partValueTG
            print("SL and TG setup after sell")
            print(slValue)
            print(tgValue)
            Positions.objects.filter(instruments=scriptCode).update(slPrice=slValue, tgPrice=tgValue, entryprice=ltp, orderId=orderId, positionType="SELL")
        
        if isFromAlgo:
            AlgoWatchlist.objects.filter(instruments = scriptCode).update(openPostion = True)
            algowatch(any)
        else:
            ManualWatchlist.objects.filter(instruments = scriptCode).update(openPostion = True)
            manualwatch(any)
    except Exception as e:
        logging.info("Order placement failed: {}".format(e.message))
        messages.error("Order placement failed: {}".format(e.message))

def tradeClose(orderId, scriptCode, isFromAlgo):
    # kite.exit_order(variety=kite.VARIETY_REGULAR, order_id=orderId)
    print("Closing trade for " + scriptCode)
    if isFromAlgo:
        AlgoWatchlist.objects.filter(instruments = scriptCode).update(openPostion = False)
    else:
        ManualWatchlist.objects.filter(instruments = scriptCode).update(openPostion = False)
    position = Positions.objects.filter(instruments = scriptCode).update(qty=0)
    if position:
        print(position.values()[0])
        
    
    


def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

# while len(liveData.keys()) != len(list(subscriberlist.keys())):
#     continue

# print("Connected to web socket")

# while datetime.time(9,15,30) >= datetime.datetime.now().time():
#     time.sleep(2)

# #strategy loop
# history = {}
# while datetime.time(9,15,30) < datetime.datetime.now().time() < datetime.time(15,15):
#     coreLogic(liveData)

