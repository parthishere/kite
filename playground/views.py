from dis import Instruction
import imp, array
# import logging
from multiprocessing import context
from pickle import FALSE, TRUE
from threading import Thread
import threading
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
from random import randint
from time import sleep
from .consumers import liveData, startLiveConnection, updateSubscriberList
from django.http import JsonResponse

# logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key=constants.KITE_API_KEY)

manualWatchlistArray = []
instrumentArray = []
positionArray = []
ordersArray = []
subscriberlist = {}
#liveData = {}
# liveData = {'ABB': {'Open': 3103.9, 'High': 3240.0, 'Low': 3054.5, 'Close': 3103.9, 'LTP': 3166.9}, 'ITC': {'Open': 359.0, 'High': 359.9, 'Low': 354.1, 'Close': 360.7, 'LTP': 356.0}, 'BPCL': {'Open': 306.0, 'High': 307.95, 'Low': 304.2, 'Close': 306.85, 'LTP': 305.5}, 'HDFC': {'Open': 2480.2, 'High': 2508.4, 'Low': 2467.8, 'Close': 2503.5, 'LTP': 2504.1}, 'RELIANCE': {'Open': 2590.0, 'High': 2596.55, 'Low': 2563.0, 'Close': 2604.0, 'LTP': 2572.5}, 'IEX': {'Open': 142.6, 'High': 142.6, 'Low': 138.85, 'Close': 142.6, 'LTP': 140.2}}
byPassZerodha = True

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
            # clearAllData()
            instrumentUpdate = Instruments.objects.filter(Q(tradingsymbol='ITC', exchange = 'NSE') | Q(tradingsymbol='HDFC', exchange = 'NSE') |  Q(tradingsymbol='RELIANCE', exchange = 'NSE') | Q(tradingsymbol='BPCL', exchange = 'NSE') | Q(tradingsymbol='ABB', exchange = 'NSE') | Q(tradingsymbol='IEX', exchange = 'NSE')).values()
            for instrumentObject in instrumentUpdate:
                tokens = instrumentObject.get('instrument_token')
                if not tokens in subscriberlist:
                    # print("Adding token to subscriber list")
                    subscriberlist[int(tokens)] = instrumentObject.get('tradingsymbol')
            # print("Subscriber list")
            # print(subscriberlist)
            getPositions()
            startLiveConnection(str(kite.access_token))
            coreLogic()
            return render(request, 'home.html', {"token": kite.access_token})
        # messages.error(request, 'Authentication Failed! Please login again')

def algowatch(request):

    #Return to home page is user is not loggedin using Zerodha
    if kite.access_token is None and byPassZerodha:
        messages.error(request, 'Authentication Failed! Please login again')
        return redirect("/")
    positionArray = getPositions()
    totalPNL = total_pnl()
    algoWatchlistArray = AlgoWatchlist.objects.all()
    # updateSubscriberList(algoWatchlistArray)
    allInstruments = list(Instruments.objects.all().values_list('tradingsymbol', flat=True))
    return render(request, 'algowatch.html', {'allInstruments':allInstruments,'algoWatchlistArray': algoWatchlistArray, 'positionArray': positionArray, 'totalPNL' : totalPNL})
    
def manualwatch(request):

    if kite.access_token is None and byPassZerodha:
        return redirect("/")
    print("----------------------------------- Manual watch")
    positionArray = getPositions()
    totalPNL = total_pnl()
    manualWatchlistArray = ManualWatchlist.objects.all()
    # updateSubscriberList(manualWatchlistArray)
    allInstruments = list(Instruments.objects.all().values_list('tradingsymbol', flat=True))
    return render(request, 'manualwatch.html', {'allInstruments':allInstruments,'manualWatchlistArray': manualWatchlistArray, 'positionArray': positionArray, 'totalPNL' : totalPNL})

# def updateSubscriberList():
#     print("asdfsadf")
    # for instrumentObject in instrumentUpdate:
    #     tokens = instrumentObject.get('instrument_token')
    #     if not tokens in subscriberlist:
    #         # print("Adding token to subscriber list")
    #         subscriberlist[int(tokens)] = instrumentObject.get('tradingsymbol')

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
        if settings_exists():
            Preferences.objects.filter(scriptName="Default").update(time=time, stoploss=stoploss, target=target, scaleupqty=scaleupqty, scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
        else:
            settings = Preferences(scriptName="Default", time=time, stoploss=stoploss, target=target, scaleupqty=scaleupqty, scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
            settings.save()
        messages.success(request, 'Preference updated successfully!')
        return render(request, 'settings.html', {'name': 'Settings'})
    else:
        settingsValues = Preferences.objects.all()
        return render(request, 'settings.html', {'settings':settingsValues})    

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

def settings_exists():
    return Preferences.objects.filter(scriptName="Default").exists()

def getPositions():
    positionsdict = kite.positions()
    positions = positionsdict['net']
    # print(positions)
    if len(positions) > 0:
        #if position is open in zerodha then update openPostion,startAlgo,exchangeType, isBuyClicked, isSellClicked, qty (check buy_quantity and sell_quantity value if both same then position is closed and if anyone is more than 0 then consider that postion is open)
        for position in positions:
            # print("Checking postion for " + position['tradingsymbol'])
            #For Open Buy position
            if int(position['quantity']) > 0: 
                print("Checking for buy postion " + position['tradingsymbol'])
                if ManualWatchlist.objects.filter(instruments=position['tradingsymbol']):
                    ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(openPostion=True, startAlgo=True, positionType="BUY", isBuyClicked=False, isSellClicked=False, qty=position['quantity'])
                else:
                    AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(openPostion=True, startAlgo=True, qty=position['quantity'])
                
                
                if not position_exists(position['tradingsymbol']):
                    #Calcualte SL and TG price for open postion and set regarding parameter for front update in Postion table
                    positionObject = Positions(instruments = position['tradingsymbol'], qty = position['quantity'], entryprice = position['buy_price'], avgTradedPrice = position['average_price'], lastTradedPrice = position['buy_price'], pnl = round(position['pnl'],2), unrealised = position['unrealised'], realised = position['realised'], startAlgo=True)
                    positionObject.save()        
                    getPositionAndUpdateModels(ltp=position['buy_price'],scriptCode=position['tradingsymbol'],orderId="",type="BUY")       
                else:
                    print("Updating New Buy Positions")
                    getPositionAndUpdateModels(ltp=position['buy_price'],scriptCode=position['tradingsymbol'],orderId="",type="BUY")
                    Positions.objects.filter(instruments = position['tradingsymbol']).update(qty = position['quantity'], avgTradedPrice = position['average_price'], lastTradedPrice = position['buy_price'], pnl = round(position['pnl'],2), unrealised = position['unrealised'], realised = position['realised'],startAlgo=True)

            #For Open sell position
            if int(position['quantity']) < 0:

                print("Checking for Sell postion " + position['tradingsymbol'])
                setQty = abs(position['quantity'])
                if ManualWatchlist.objects.filter(instruments=position['tradingsymbol']):
                    ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(openPostion=True, startAlgo=True, positionType="SELL", isBuyClicked=False, isSellClicked=False, qty=setQty)
                else:
                    AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(openPostion=True, startAlgo=True, qty=setQty)

                if not position_exists(position['tradingsymbol']):
                    #Calcualte SL and TG price for open postion and set regarding parameter for front update in Postion table
                    positionObject = Positions(instruments = position['tradingsymbol'], qty = position['quantity'], entryprice = position['sell_price'], avgTradedPrice = position['average_price'], lastTradedPrice = position['sell_price'], pnl = round(position['pnl'],2), unrealised = position['unrealised'], realised = position['realised'], startAlgo=True)
                    positionObject.save()        
                    getPositionAndUpdateModels(ltp=position['sell_price'],scriptCode=position['tradingsymbol'],orderId="",type="SELL")       
                else:
                    print("Updating New Sell Positions")
                    print(position['sell_price'])
                    getPositionAndUpdateModels(ltp=position['sell_price'],scriptCode=position['tradingsymbol'],orderId="",type="SELL")
                    Positions.objects.filter(instruments = position['tradingsymbol']).update(qty = position['quantity'], avgTradedPrice = position['average_price'], lastTradedPrice = position['sell_price'], pnl = round(position['pnl'],2), unrealised = position['unrealised'], realised = position['realised'],startAlgo=True)
            
            #For Closed Positions
            if int(position['quantity']) == 0:  
                ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(openPostion=False, startAlgo=False, positionType="", isBuyClicked=False, isSellClicked=False, qty = 1)
                AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(openPostion=False, startAlgo=False, qty = 1)
                # print("Checking for closed postion " + position['tradingsymbol'])   
                if not position_exists(position['tradingsymbol']):
                    positionObject = Positions(instruments = position['tradingsymbol'], qty = position['quantity'], entryprice = 0.0, avgTradedPrice = position['average_price'], lastTradedPrice = position['last_price'], pnl = round(position['pnl'],2), unrealised = position['unrealised'], realised = position['realised'], startAlgo=False)
                    positionObject.save()        
                else:
                    # print("Updating New Positions")
                    Positions.objects.filter(instruments = position['tradingsymbol']).update(qty = position['quantity'], avgTradedPrice = position['average_price'], lastTradedPrice = position['last_price'], pnl = round(position['pnl'],2), unrealised = position['unrealised'], realised = position['realised'], startAlgo=False)
    else:
        print("No postion available")
    
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
    if total:
        return round(total,2)

#=========================
## Algo Core Logic Method
#=========================
#Steps for the logic


def coreLogic(): #A methond to check 
    # print(liveData,"++++++++++++++++++++++++coming from corelogic consumers")
    threading.Timer(1.0, coreLogic).start()
    watchForAlgowatchlistBuySellLogic()
    watchForManualListBuySellLogic()

def watchForAlgowatchlistBuySellLogic():

    # print(liveData,"++++++++++++++++++++++++coming from watchforalgo consumers testing again")
    algoArray = AlgoWatchlist.objects.all()
    # print(algoArray, "++++++++++++++++Algo Array Values=============")

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

        # print(items.instruments,"++++++++++++++++++++++++coming from watchforalgo consumers")
        # print(liveData,"++++++++++++++++++++++++coming from watchforalgo consumers")
        if items.instruments in liveData:
            liveValues = liveData[items.instruments]
            #UBL : #then UBL(Upper band limit)) is 2448 (2% of 2400, 2400 + 48 = 2448)
            partValue = (ordp*liveValues['Open'])/100
            ubl = liveValues['Open'] + partValue
            #LBL : #then LBL(Lower band limit)) is 2352 (2% of 2400, 2400 - 48 = 2352)
            lbl = liveValues['Open'] - partValue
            # #SLHit: 0 #Counter for SL Hit for particualr script
            # print("Checking algo for " + items.instruments)
            if items.startAlgo and not items.openPostion: #IF_Check if Algo is started and Not any positon open for that script
                if ordtick: #IF_ORD True check if open is in range
                    if (liveValues['LTP'] > liveValues['Open']) and (liveValues['LTP'] < ubl and liveValues['LTP'] > lbl): #IF_check CMP > OPEN and (CMP > LBL and CMP > UPL)
                        print("Opening range is selected so only checking both ltp > Open and ltp in in range")
                        tradeInitiateWithSLTG(type="BUY", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=False)
                    elif (liveValues['LTP'] < liveValues['Open']) and (liveValues['LTP'] < ubl and liveValues['LTP'] > lbl): #ELSE_#check CMP < OPEN and (CMP > LBL and CMP > UPL)
                        print("Opening range is selected so only checking both ltp < Open and ltp in in range")
                        tradeInitiateWithSLTG(type="SELL", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=False)
                else: #ELSE_ORD False means do not check if open is in range 
                    if liveValues['LTP'] > liveValues['Open']: #IF_check CMP > OPEN
                        print("Opening range is not selected so only checking ltp > Open")
                        tradeInitiateWithSLTG(type="BUY", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=False)
                    elif liveValues['LTP'] < liveValues['Open']: #ELSE_#check CMP < OPEN
                        print("Opening range is not selected so only checking ltp < Open")
                        tradeInitiateWithSLTG(type="SELL", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=False)
                    
            elif items.startAlgo and items.openPostion: #ELSEIF_check if Algo is started and Position Open (Either Buy or Sell)
                postions = Positions.objects.filter(instruments=items.instruments)
                if postions:
                    potionObject = postions.values()[0]
                    print("SL Price = " + str(potionObject['slPrice']))
                    print("TG Price = " + str(potionObject['tgPrice']))
                    print("Current Price = " + str(liveValues['LTP']))
                    print("Next Qty to trade ============================= ", items.qty)
                    if potionObject['positionType'] == "BUY": #IF_check if position is BUY and 
                        finalQty = 0
                        if liveValues['LTP'] <= potionObject['slPrice']:
                            if items.qty >= potionObject['qty']:
                                finalQty = items.qty
                            else:
                                finalQty = (potionObject['qty'])*2
                            print("Final Qty to trade ============================= ", finalQty)
                            tradeInitiateWithSLTG(type="SELL", scriptQty=finalQty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=False)                                
                            slCount = items.slHitCount + 1
                            AlgoWatchlist.objects.filter(instruments = items.instruments).update(slHitCount=slCount)
                        elif liveValues['LTP'] >= potionObject['tgPrice']: #IF CMP >= TG
                            tradeInitiateWithSLTG(type="SELL", scriptQty=potionObject['qty'], exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
                        else:
                            print("Position BUYALGO, No SL, No TG so continue")
                    elif potionObject['positionType'] == "SELL":#ELSE_check if positino is SELL
                        if liveValues['LTP'] >= potionObject['slPrice']: #if CMP >= SL
                            if items.qty > potionObject['qty']:
                                finalQty = items.qty
                            else:
                                finalQty = (potionObject['qty'])*2
                            tradeInitiateWithSLTG(type="BUY", scriptQty=finalQty, exchangeType=items.exchangeType,sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=False)
                            slCount = items.slHitCount + 1
                            AlgoWatchlist.objects.filter(instruments = items.instruments).update(slCount)
                        elif liveValues['LTP'] <= potionObject['tgPrice']: #IF CMP <= TG
                            tradeInitiateWithSLTG(type="BUY", scriptQty=potionObject['qty'], exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
                        else:
                            print("Position SELLALGO, No SL, No TG so continue")
            elif not items.startAlgo and items.openPostion: #ELSE_check if algo is stopped and Position Open (Either Buy or Sell)
                postions = Positions.objects.filter(instruments=items.instruments)
                if postions:
                    potionObject = postions.values()[0]
                    print("Not SL ot TG achived but manuaaly - Close Postions and stop algo")
                    print(postions)
                    AlgoWatchlist.objects.filter(instruments = items.instruments).update(openPostion = False)
                    if potionObject['positionType'] == "BUY":
                            tradeInitiateWithSLTG(type="SELL", scriptQty=potionObject['qty'], exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
                    if potionObject['positionType'] == "SELL":
                            tradeInitiateWithSLTG(type="BUY", scriptQty=potionObject['qty'], exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
            # else:
            #     print("Nothing to trade from Algo Watchlist for " + items.instruments) 
        # else:
        #     print("Key not exist in live data")        
    # print("No script found to trade")

def watchForManualListBuySellLogic():

    # print(liveData,"++++++++++++++++++++++++coming from watchformanual consumers")
    manualArray = ManualWatchlist.objects.all()
    settings = Preferences.objects.all()
    #TG : Get % value from settings
    tg = settings.values()[0]['target']
    #SL : Get % value from settings
    sl = settings.values()[0]['stoploss']

    for items in manualArray: #Reliance

        # print("Checking manual for " + items.instruments)
        # print("Live Datas")
        # print(liveData)
        if items.instruments in liveData:
            liveValues = liveData[items.instruments]
            if items.startAlgo and not items.openPostion:
                if items.isBuyClicked:   #IF_Buy_Clicked then Place buy order no condition need to check
                    print("Buying Manually")
                    tradeInitiateWithSLTG(type="BUY", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, orderId="", ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, isCloseTrade=False)
                elif items.isSellClicked:
                    print("Selling Manually")
                    tradeInitiateWithSLTG(type="SELL", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg, orderId="", ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, isCloseTrade=False) 
                else:
                    print("Nothing to trade from Manual Watchlist")
            elif items.startAlgo and items.openPostion:

                print("Algo is running and postion is also running so checking for SL or TG +++++++++++++++++++++++======__________________________________")
                postions = Positions.objects.filter(instruments=items.instruments)
                if postions:
                    potionObject = postions.values()[0]
                    print("SL Price = " + str(potionObject['slPrice']))
                    print("TG Price = " + str(potionObject['tgPrice']))
                    print("Current Price = " + str(liveValues['LTP']))
                    print("Current Postion = " + str(potionObject['positionType']))
                    print("Next Qty to trade ============================= ", items.qty)
                    if potionObject['positionType'] == "BUY": #IF_check if position is BUY and 
                        if liveValues['LTP'] <= potionObject['slPrice']:
                            print("SL Hit, double the qty")
                            finalQty = 0
                            if items.qty > potionObject['qty']:
                                finalQty = items.qty
                            else:
                                finalQty = (potionObject['qty'])*2

                            print("Final Qty to trade ============================= ", items.qty)
                            tradeInitiateWithSLTG(type="SELL", scriptQty=finalQty, exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId="", isCloseTrade=False)
                            slCount = items.slHitCount + 1
                            ManualWatchlist.objects.filter(instruments = items.instruments).update(slHitCount=slCount)
                        elif liveValues['LTP'] >= potionObject['tgPrice']: #IF CMP >= TG
                            print("Target Achived so Close Postions and stop algo")
                            tradeInitiateWithSLTG(type="SELL", scriptQty=potionObject['qty'], exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
                        else:
                            print("Position BUYMANUAL, No SL, No TG so continue")
                    elif potionObject['positionType'] == "SELL":#ELSE_check if positino is SELL
                        if liveValues['LTP'] >= potionObject['slPrice']: #if CMP >= SL
                            print("SL Hit, double the qty")
                            finalQty = 0
                            if items.qty >= potionObject['qty']:
                                finalQty = items.qty
                            else:
                                finalQty = (potionObject['qty'])*2
                            tradeInitiateWithSLTG(type="BUY", scriptQty=finalQty, exchangeType=items.exchangeType,sl=sl, tg=tg,orderId="", ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, isCloseTrade=False)
                            slCount = items.slHitCount + 1
                            ManualWatchlist.objects.filter(instruments = items.instruments).update(slCount)
                        elif liveValues['LTP'] <= potionObject['tgPrice']: #IF CMP <= TG
                            print("Target achived so Close Postions and stop algo")
                            tradeInitiateWithSLTG(type="BUY", scriptQty=potionObject['qty'], exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
                        else:
                            print("Position SELLMANUAL, No SL, No TG so continue")
            elif not items.startAlgo and items.openPostion:
                print("Algo is stopped and postion is running so closing the trade")
                postions = Positions.objects.filter(instruments=items.instruments)
                if postions:
                    potionObject = postions.values()[0]
                    print("Not SL ot TG achived but manuaaly - Close Postions and stop algo")
                    if potionObject['positionType'] == "BUY":
                        tradeInitiateWithSLTG(type="SELL", scriptQty=potionObject['qty'], exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
                    if potionObject['positionType'] == "SELL":
                        tradeInitiateWithSLTG(type="BUY", scriptQty=potionObject['qty'], exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
            # else:
            #     print("Nothing to trade in Manual Watchlist")
        # else:
        #     print("Key not existing in live data, Wating for live data")
        
#=========================
## Algo Commonn Methods
#=========================

def scaleUpQty(request):
    script= request.POST['script']
    qty= request.POST['scriptQty']
    isFromAlgo = request.POST['isFromAlgoTest']
    print("Updated QTY ===========+++++++",script, qty)
    if isFromAlgo:
        AlgoWatchlist.objects.filter(instruments = script).update(qty = qty)
    else:
        ManualWatchlist.objects.filter(instruments = script).update(qty = qty)
    return None

def scaleDownQty(request):
    script= request.POST['script']
    qty= request.POST['scriptQty']
    isFromAlgo = request.POST['isFromAlgoTest']
    print("Updated QTY ===========+++++++", script, qty)
    if isFromAlgo:
        AlgoWatchlist.objects.filter(instruments = script).update(qty = qty)
    else:
        ManualWatchlist.objects.filter(instruments = script).update(qty = qty)
    return None

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def deleteInstrument(request):
    script= request.POST['script']
    flag = request.POST['flag']
    if flag == "ManualWatch":
        ManualWatchlist.objects.filter(instruments=script).delete()
    elif flag == "AlgoWatch":
        AlgoWatchlist.objects.filter(instruments=script).delete()
    
    instrumentObject = Instruments.objects.filter(tradingsymbol = script).values()
    instumentData = instrumentObject[0]
    updateSubscriberList(instumentData["instrument_token"], instumentData["tradingsymbol"], False)
    return HttpResponse("success")

@csrf_exempt
def addInstrument(request):
    print("Came from JS to Add Instrument ==============" + request.POST['script'])
    script= request.POST['script']
    flag = request.POST['flag']
    instrumentObject = Instruments.objects.filter(tradingsymbol = script).values()
    instumentData = instrumentObject[0]
    print(instumentData["instrument_token"])
    print(instumentData["tradingsymbol"])
    updateSubscriberList(instumentData["instrument_token"], instumentData["tradingsymbol"], True)
    if flag == "ManualWatch":
        instrumentObjectToManualWatchlistObject(instrumentObject)
        manualWatchObject = ManualWatchlist.objects.filter(instruments=script).values()
        return JsonResponse({"instrument":list(manualWatchObject)})
    elif flag == "AlgoWatch":
        instrumentObjectToAlgoWatchlistObject(instrumentObject)
        algoWatchObject = AlgoWatchlist.objects.filter(instruments=script).values()
        return JsonResponse({"instrument":list(algoWatchObject)})


def buySingle(request): #For Manual watchlist
    print("Came from JS to buy single" + request.POST['script'])
    print("Came from JS to start" + request.POST['scriptQty'])
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(startAlgo = True)
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(qty = int(request.POST['scriptQty']))
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(isBuyClicked = True)
    return render(request, 'algowatch.html')
    # return HttpResponse(request.POST['script'])

def sellSingle(request): #For Manual watchlist
    print("Came from JS to sell single" + request.POST['script'])
    print("Came from JS to start" + request.POST['scriptQty'])
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(startAlgo = True)
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(qty = int(request.POST['scriptQty']))
    ManualWatchlist.objects.filter(instruments = request.POST['script']).update(isSellClicked = True)
    return HttpResponse(request.POST['text'])

def startSingle(request): #For Manual watchlist
    # print(liveData,"++++++++++++++++++++++++coming from consumers")
    print("Came from JS to start" + request.POST['script'],)
    AlgoWatchlist.objects.filter(instruments = request.POST['script']).update(startAlgo = True)
    AlgoWatchlist.objects.filter(instruments = request.POST['script']).update(qty = int(request.POST['scriptQty']))
    return HttpResponse(request.POST['script'])
    
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
    return HttpResponse(request.POST['script'])

def tradeInitiateWithSLTG(type, exchangeType, scriptQty, scriptCode, ltp, sl, tg, isFromAlgo, orderId, isCloseTrade):
    #type should be "BUY" or "SELL"
    #exchangeType should be "NFO" or "NSE"
    print(type)
    print(exchangeType)
    print(scriptQty)
    print(scriptCode)
    print(ltp)
    print(sl)
    print(tg)
    print(isFromAlgo)
    print(orderId)
    print(isCloseTrade)
    #Place order (with ScriptQTY)
    try:
        
        orderId = ""
        
        if not isCloseTrade:

            orderId = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchangeType, 
                    tradingsymbol=scriptCode, transaction_type=type, quantity=abs(scriptQty),
                    product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_MARKET, validity=kite.VALIDITY_DAY)
            print("Order places successfully=================")
            if isFromAlgo:
                print("Algo Open Position Updated=================")
                AlgoWatchlist.objects.filter(instruments = scriptCode).update(openPostion = True)
                AlgoWatchlist.objects.filter(instruments = scriptCode).update(entryprice = ltp)
            else:
                print("Manual Open Position Updated++++++++++++")
                ManualWatchlist.objects.filter(instruments = scriptCode).update(openPostion = True)
                ManualWatchlist.objects.filter(instruments = scriptCode).update(entryprice = ltp)
            orderId = format(orderId)
            # orderId = random_with_N_digits(4)
            getPositions()
            getPositionAndUpdateModels(ltp,scriptCode, orderId, type)
        else:

            print("Order not places successfully=============================")
            orderId = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchangeType, 
                    tradingsymbol=scriptCode, transaction_type=type, quantity=abs(scriptQty),
                    product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_MARKET, validity=kite.VALIDITY_DAY)
            if isFromAlgo:
                AlgoWatchlist.objects.filter(instruments = scriptCode).update(openPostion = False)
            else:
                ManualWatchlist.objects.filter(instruments = scriptCode).update(openPostion = False)

            getPositions()
            if position_exists(scriptCode):
                Positions.objects.filter(instruments = scriptCode).update(qty=0)
    except Exception as e:
        # logging.info("Order placement failed ")
        if isFromAlgo:
            AlgoWatchlist.objects.filter(instruments = scriptCode).update(openPostion = False)
            AlgoWatchlist.objects.filter(instruments = scriptCode).update(startAlgo = False)
        else:
            ManualWatchlist.objects.filter(instruments = scriptCode).update(openPostion = False)
            ManualWatchlist.objects.filter(instruments = scriptCode).update(startAlgo = False)
        
def getPositionAndUpdateModels(ltp, scriptCode, orderId, type):
    if type == "BUY":
        result = calculateSLTGPrice(ltp, type)
        print("Modified SL Price= " + str(result[0]))
        print("Modified TG Price= " + str(result[1]))
        if position_exists(scriptCode):
            Positions.objects.filter(instruments=scriptCode).update(slPrice=result[0], tgPrice=result[1], entryprice=ltp, orderId=orderId, positionType="BUY")
    else:
        result = calculateSLTGPrice(ltp, type)
        print("Modified SL Price= " + str(result[0]))
        print("Modified TG Price= " + str(result[1]))
        if position_exists(scriptCode):
            Positions.objects.filter(instruments=scriptCode).update(slPrice=result[0], tgPrice=result[1], entryprice=ltp, orderId=orderId, positionType="SELL")

def calculateSLTGPrice(ltp, type):
    settings = Preferences.objects.all()
    #TG : Get % value from settings
    tg = settings.values()[0]['target']
    #SL : Get % value from settings
    sl = settings.values()[0]['stoploss']
    if type == "BUY":
        partValueSL = (sl*ltp)/100
        partValueTG = (tg*ltp)/100
        slValue = ltp - partValueSL
        tgValue = ltp + partValueTG
        # print("SL and TG setup after Buy")
        # print(slValue)
        # print(tgValue)
        return slValue, tgValue
    else:
        partValueSL = (sl*ltp)/100
        partValueTG = (tg*ltp)/100
        slValue = ltp + partValueSL
        tgValue = ltp - partValueTG
        # print("SL and TG setup after sell")
        # print(slValue)
        # print(tgValue)
        return slValue, tgValue

def stopAll(request):
    print("Came from JS to stop All")
    algoArray = AlgoWatchlist.objects.all()
    for items in algoArray:
        AlgoWatchlist.objects.filter(instruments = items.instruments).update(startAlgo = False)
        # AlgoWatchlist.objects.filter(instruments = items.instruments).update(qty = int(request.POST['scriptQty']))
    return HttpResponse()

def startAll(request):
    print("Came from JS to start All")
    algoArray = AlgoWatchlist.objects.all()
    print(len(algoArray))
    for items in algoArray:
        print("Starting for all items: ", items.instruments)
        AlgoWatchlist.objects.filter(instruments = items.instruments).update(startAlgo = True)
        AlgoWatchlist.objects.filter(instruments = items.instruments).update(qty = int(request.POST['scriptQty']))
    return HttpResponse()

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

