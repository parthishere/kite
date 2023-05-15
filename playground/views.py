from django.views.decorators.csrf import csrf_exempt
from dis import Instruction
import imp
import array
import pytz
# import logging
from multiprocessing import context
from pickle import FALSE, TRUE
from threading import Thread
import threading
from urllib import response
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from playground.models import DateTimeCheck, Preferences, Instruments, AlgoWatchlist, ManualWatchlist, Positions, Orders
from django.contrib import messages
from kiteconnect import KiteConnect, KiteTicker
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from json import dumps
from django.db.models import Q
from django.db.models import Sum
import datetime
import time
from random import randint
from time import sleep
from .consumers import liveData, startLiveConnection, updateSubscriberList, updatePostions, updatePNL
from django.http import JsonResponse
from datetime import datetime, date, timedelta, time as dt_time
from time import gmtime, strftime
import logging
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
import pyotp
from playground import consumers

from django.conf import settings as st

kite = KiteConnect(api_key=st.KITE_API_KEY)
manualWatchlistArray = []
instrumentArray = []
positionArray = []
ordersArray = []
subscriberlist = consumers.subscriberlist 
positiondict = {}
timeToStart = 0.0
# liveData = {}
# liveData = {'ABB': {'Open': 3103.9, 'High': 3240.0, 'Low': 3054.5, 'Close': 3103.9, 'LTP': 3166.9}, 'ITC': {'Open': 359.0, 'High': 359.9, 'Low': 354.1, 'Close': 360.7, 'LTP': 356.0}, 'BPCL': {'Open': 306.0, 'High': 307.95, 'Low': 304.2, 'Close': 306.85, 'LTP': 305.5}, 'HDFC': {'Open': 2480.2, 'High': 2508.4, 'Low': 2467.8, 'Close': 2503.5, 'LTP': 2504.1}, 'RELIANCE': {'Open': 2590.0, 'High': 2596.55, 'Low': 2563.0, 'Close': 2604.0, 'LTP': 2572.5}, 'IEX': {'Open': 142.6, 'High': 142.6, 'Low': 138.85, 'Close': 142.6, 'LTP': 140.2}}
coreLogicLock = threading.Lock()
coreRunning = False

# =========================
# All Views Functions
# =========================


def index(request: HttpRequest):
    return render(request, 'index.html', context={'api_key': st.KITE_API_KEY})


def login_in_zerodha(api_key, api_secret, user_id, user_pwd, totp_key):
    driver = uc.Chrome()
    driver.get(f'https://kite.trade/connect/login?api_key={api_key}&v=3')
    login_id = WebDriverWait(driver, 10).until(
        lambda x: x.find_element(By.XPATH, '//*[@id="userid"]'))
    login_id.send_keys(user_id)

    pwd = WebDriverWait(driver, 10).until(
        lambda x: x.find_element(By.XPATH, '//*[@id="password"]'))
    pwd.send_keys(user_pwd)

    submit = WebDriverWait(driver, 10).until(lambda x: x.find_element(
        By.XPATH, '//*[@id="container"]/div/div/div[2]/form/div[4]/button'))
    submit.click()

    time.sleep(1)
    # adjustment to code to include totp
    totp = WebDriverWait(driver, 10).until(
        lambda x: x.find_element(By.XPATH, '//*[@id="totp"]'))
    authkey = pyotp.TOTP(totp_key)
    totp.send_keys(authkey.now())
    # adjustment complete

    continue_btn = WebDriverWait(driver, 10).until(lambda x: x.find_element(
        By.XPATH, '//*[@id="container"]/div/div/div[2]/form/div[3]/button'))
    continue_btn.click()

    time.sleep(5)

    url = driver.current_url
    initial_token = url.split('request_token=')[1]
    request_token = initial_token.split('&')[0]

    driver.close()

    kite = KiteConnect(api_key=api_key)
    print(request_token)
    data = kite.generate_session(request_token, api_secret=api_secret)
    kite.set_access_token(data['access_token'])

    return kite


def home(request):

    print('In Home Page with access token = %s', kite.access_token)
    if kite.access_token is None:
        return redirect("/")

    TimeObjData = DateTimeCheck.objects.all()
    if TimeObjData.exists():
        TimeObj = TimeObjData.first()
        todayDate = (datetime.now() + timedelta(hours=5, minutes=30)).date()
        if TimeObj.dateCheck != todayDate:
            TimeObjData.update(dateCheck=todayDate)
            clearAllData()
            fetchInstrumentInBackground()
    algoWatchlistArray = AlgoWatchlist.objects.all()
    manualWatchlistArray = ManualWatchlist.objects.all()
    updateSavedSubscriberList(algoWatchlistArray.values())
    updateSavedSubscriberList(manualWatchlistArray.values())
    return render(request, 'home.html')


def loginWithZerodha(request):

    print("In auto login function")
    topt = pyotp.TOTP('ZF3MONJ23XF34ESGSGRXOKR6RGTRQLXN')
    toptKey = topt.now()
    logging.warning("TOTD: %s", toptKey)
    kiteobj = login_in_zerodha(
        st.KITE_API_KEY, st.KITE_API_SECRET, 'LN7447', 'zzzzaaaa', toptKey)
    print(kiteobj.profile())
    return HttpResponse("success")


def loginUser(request):
    if request.method == 'GET':
        if request.GET['request_token'] != "":
            data = kite.generate_session(
                request.GET['request_token'], api_secret=st.KITE_API_SECRET)
            kite.set_access_token(data["access_token"])
            logging.warning("Access token===== %s", data["access_token"])
            startLiveConnection(str(kite.access_token))
            coreLogic()
            return redirect('Home')


def algowatch(request):
    logging.warning('Access token in algowatch===== %s', kite.access_token)
    # Return to home page is user is not loggedin using Zerodha
    if kite.access_token is None:
        return redirect("/")

    positionArray = getPositions()
    print(positionArray,'----')
    totalPNL = total_pnl() or 0
    algoWatchlistArray = AlgoWatchlist.objects.all()
    allInstruments = list(Instruments.objects.all(
    ).values_list('tradingsymbol', flat=True))
    #print(allInstruments)
   
   

    return render(request, 'algowatch.html', {'allInstruments': allInstruments, 'algoWatchlistArray': algoWatchlistArray, 'positionArray': positionArray, 'totalPNL': totalPNL})


def manualwatch(request):

    logging.warning('Access token in manualwatch===== %s', kite.access_token)
    if kite.access_token is None:
        return redirect("/")
    positionArray = getPositions()
    totalPNL = total_pnl()
    manualWatchlistArray = ManualWatchlist.objects.all()
    allInstruments = list(Instruments.objects.all(
    ).values_list('tradingsymbol', flat=True))
    return render(request, 'manualwatch.html', {'allInstruments': allInstruments, 'manualWatchlistArray': manualWatchlistArray, 'positionArray': positionArray, 'totalPNL': totalPNL})


def updateSavedSubscriberList(instrumentArray):
    for instrumentObject in instrumentArray:
        tokens = instrumentObject.get('instrumentsToken')
        updateSubscriberList(
            int(tokens), instrumentObject.get('instruments'), True)

def orders(request):

    logging.warning('Access token in orders===== %s', kite.access_token)
    if kite.access_token is None:
        return redirect("/")

    ordersArray = getOrders()
    # print(orderArray)
    # print(orderArray.values().count())
    # print(ordersArray.values()[1]['orderId'])
    return render(request, 'orders.html', {'orderArrayList': ordersArray})


def settings(request):
    if kite.access_token is None:
        return redirect("/")

    if request.method == "POST":
        time = datetime.strptime(request.POST.get('time'), '%H:%M:%S')
        stoploss = request.POST.get('stoploss')
        target = request.POST.get('target')
        scaleupqty = request.POST.get('scaleupqty')
        scaledownqty = request.POST.get('scaledownqty')
        openingrange = request.POST.get('openingrange')
        openingrangebox = request.POST.get('openingrangebox')
        if settings_exists():
            Preferences.objects.filter(scriptName="Default").update(time=time, stoploss=stoploss, target=target,
                                                                    scaleupqty=scaleupqty, scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
        else:
            settings = Preferences(scriptName="Default", time=time, stoploss=stoploss, target=target, scaleupqty=scaleupqty,
                                   scaledownqty=scaledownqty, openingrange=openingrange, openingrangebox=openingrangebox)
            settings.save()
        messages.success(request, 'Preference updated successfully!')
        return render(request, 'settings.html', {'name': 'Settings'})
    else:
        settingsValues = Preferences.objects.all()
        return render(request, 'settings.html', {'settings': settingsValues})

def logoutUser(request):
    kite.invalidate_access_token()
    kite.set_access_token(None)
    logging.warning('Logout called = %s', kite.access_token)
    kite.invalidate_access_token()
    return redirect("/")

# =========================
# All Supported Functions
# =========================


def clearAllData():
    print("Cleaning old data and updating instrument list")
    # Instruments.objects.all().delete()
    AlgoWatchlist.objects.all().delete()
    ManualWatchlist.objects.all().delete()
    Positions.objects.all().delete()
    Orders.objects.all().delete()


def on_done():
    print("Data downloading finished================++++++++++++++++++")


def fetchInstrumentInBackground():
    # do some stuff
    download_thread = threading.Thread(
        target=refreshIntrumentList, name="Downloader")
    download_thread.start()


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
            print(item)
            print("Updating instruments")
            instrumentUpdate = Instruments.objects.get(
                tradingsymbol=tradingsymbol)
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
            print(item)
            print("Adding instruments")
            instrumentModel = Instruments(instrument_token=instrument_token, exchange_token=exchange_token, tradingsymbol=tradingsymbol, name=name,
                                          expiry=expiry, tick_size=tick_size, strike=strike, lot_size=lot_size, instrument_type=instrument_type, segment=segment, exchange=exchange)
            instrumentModel.save()

def instrumentObjectToManualWatchlistObject(instrumentUpdate):
    for instrumentObject in instrumentUpdate:
        tradingSymbol = instrumentObject.get('tradingsymbol')
        if not ManualWatchlist.objects.filter(instruments=tradingSymbol).exists():
            manualWatlistObject = ManualWatchlist(instruments=tradingSymbol, instrumentsToken=instrumentObject.get('instrument_token'),
                                                  exchangeType=instrumentObject.get('exchange'), segment=instrumentObject.get('segment'), instrumentType=instrumentObject.get('instrument_type'), qty=instrumentObject.get('lot_size'))
            manualWatlistObject.save()


def instrumentObjectToAlgoWatchlistObject(instrumentUpdate):
    for instrumentObject in instrumentUpdate:
        tradingSymbol = instrumentObject.get('tradingsymbol')
        if not AlgoWatchlist.objects.filter(instruments=tradingSymbol).exists():
            algoWatlistObject = AlgoWatchlist(instruments=tradingSymbol, instrumentsToken=instrumentObject.get('instrument_token'),
                                              exchangeType=instrumentObject.get('exchange'), segment=instrumentObject.get('segment'), instrumentType=instrumentObject.get('instrument_type'), qty=instrumentObject.get('lot_size'))
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
    

    for pos in range(len(positionsdict['net'])):
        if (l_data := liveData.get(positionsdict['net'][pos]['tradingsymbol'])):
            pnl = (positionsdict['net'][pos]['sell_value']-positionsdict['net'][pos]['buy_value']) + (positionsdict['net'][pos]['multiplier']*l_data['LTP']*positionsdict['net'][pos]['quantity'])
            positionsdict['net'][pos]['pnl']=round(float(pnl),2)
            #positionsdict['net'][pos]['pnl']="+{}".format(round(float(pnl),2)) if float(pnl) > 0 else round(float(pnl),2) 

            if positionsdict['net'][pos]['quantity'] != 0 :             # used for % profit 
                    positionsdict['net'][pos]['last_price']  = ( positionsdict['net'][pos]['pnl'] / (positionsdict['net'][pos]['average_price']*0.20*positionsdict['net'][pos]['quantity']) )*100 
            else :
                    if positionsdict['net'][pos]['buy_quantity'] != 0 :
                        positionsdict['net'][pos]['last_price']  = (( positionsdict['net'][pos]['day_sell_price'] - positionsdict['net'][pos]['day_buy_price'] )*100*5*positionsdict['net'][pos]['day_buy_quantity'])/ positionsdict['net'][pos]['day_buy_price']

            if positionsdict['net'][pos]['quantity']==0 :
                positionsdict['net'][pos]['average_price']= positionsdict['net'][pos]['pnl']
            else:
                positionsdict['net'][pos]['average_price']=  positionsdict['net'][pos]['pnl']/positionsdict['net'][pos]['quantity']

            if positionsdict['net'][pos]['quantity']< 0 :
                if positionsdict['net'][pos]['pnl'] < 0 :
                    positionsdict['net'][pos]['average_price'] = 0 - positionsdict['net'][pos]['average_price'] 

            

                
    #print(positionsdict)
    updatePostions(positionsdict)
    positions = positionsdict['net']
    entryPrice = 0.0

    if len(positions) > 0:
        # if position is open in zerodha then update openPostion,startAlgo,exchangeType, isBuyClicked, isSellClicked, qty (check buy_quantity and sell_quantity value if both same then position is closed and if anyone is more than 0 then consider that postion is open)
        for position in positions:

            pnl = position['pnl']

            # For Open Buy position
            if int(position['quantity']) > 0:
                # print("Checking for buy postion " + position['tradingsymbol'])

                if ManualWatchlist.objects.filter(instruments=position['tradingsymbol']):
                    ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                        openPostion=True, startAlgo=True, positionType="BUY", isBuyClicked=False, isSellClicked=False)  # qty=position['quantity']
                    entryPrice = float(ManualWatchlist.objects.filter(
                        instruments=position['tradingsymbol']).values()[0]["entryprice"])
                elif AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']):
                    AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                        openPostion=True, startAlgo=True)
                    entryPrice = float(AlgoWatchlist.objects.filter(
                        instruments=position['tradingsymbol']).values()[0]["entryprice"])

                if not position_exists(position['tradingsymbol']):
                    # Calcualte SL and TG price for open postion and set regarding parameter for front update in Postion table
                    positionObject = Positions(instruments=position['tradingsymbol'], qty=position['quantity'], avgTradedPrice=round(
                        position['average_price'], 2), pnl=round(pnl, 3), startAlgo=True)
                    positionObject.save()
                    getPositionAndUpdateModels(
                        ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="BUY")
                else:
                    # print("Updating New Buy Positions")
                    getPositionAndUpdateModels(
                        ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="BUY")
                    Positions.objects.filter(instruments=position['tradingsymbol']).update(qty=position['quantity'], avgTradedPrice=round(
                        position['average_price'], 2), pnl=round(pnl, 3), startAlgo=True)

            # For Open sell position
            elif int(position['quantity']) < 0:
                # print("Checking for Sell postion " + position['tradingsymbol'])
                setQty = abs(position['quantity'])

                if ManualWatchlist.objects.filter(instruments=position['tradingsymbol']):
                    ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                        openPostion=True, startAlgo=True, positionType="SELL", isBuyClicked=False, isSellClicked=False)  # , qty=setQty
                    entryPrice = float(ManualWatchlist.objects.filter(
                        instruments=position['tradingsymbol']).values()[0]["entryprice"])
                elif AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']):
                    AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                        openPostion=True, startAlgo=True)
                    entryPrice = float(AlgoWatchlist.objects.filter(
                        instruments=position['tradingsymbol']).values()[0]["entryprice"])

                if not position_exists(position['tradingsymbol']):
                    # Calcualte SL and TG price for open postion and set regarding parameter for front update in Postion table
                    positionObject = Positions(instruments=position['tradingsymbol'], qty=position['quantity'], avgTradedPrice=round(
                        position['average_price'], 2), pnl=round(pnl, 3), startAlgo=True)
                    positionObject.save()
                    getPositionAndUpdateModels(
                        ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="SELL")
                else:
                    # print("Updating New Sell Positions")
                    getPositionAndUpdateModels(
                        ltp=entryPrice, scriptCode=position['tradingsymbol'], orderId="", type="SELL")
                    Positions.objects.filter(instruments=position['tradingsymbol']).update(qty=position['quantity'], avgTradedPrice=round(
                        position['average_price'], 2), pnl=round(float(pnl), 3), startAlgo=True)

            # For Closed Positions
            elif int(position['quantity']) == 0:
                ManualWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                    openPostion=False, startAlgo=False, positionType="", isBuyClicked=False, isSellClicked=False)
                # print("will be called ++++++++++++++++++++ 1")
                AlgoWatchlist.objects.filter(instruments=position['tradingsymbol']).update(
                    openPostion=False, startAlgo=False)
                # print("Checking for closed postion " + position['tradingsymbol'])
                if not position_exists(position['tradingsymbol']):
                    print(pnl,'not posi')
                    # print("will be called ++++++++++++++++++++ 2")
                    positionObject = Positions(instruments=position['tradingsymbol'], qty=position['quantity'], entryprice=0.0, avgTradedPrice=round(position['average_price'], 2), lastTradedPrice=round(
                        position['last_price'], 2), pnl=pnl, unrealised=position['unrealised'], realised=position['realised'], startAlgo=False)
                    positionObject.save()
                else:
                    # print("Updating New Positions",pnl)
                    # print("will be called ++++++++++++++++++++ 3")
                    Positions.objects.filter(instruments=position['tradingsymbol']).update(qty=position['quantity'], avgTradedPrice=round(position['average_price'], 2), lastTradedPrice=round(
                        position['last_price'], 2), pnl=pnl, unrealised=position['unrealised'], realised=position['realised'], startAlgo=False)
    # else:
    #     print("No postion available")

    return Positions.objects.all()


def getOrders():
    orders = kite.orders()
    # print(ordersdict)
    # orders = ordersdict['data']

    for order in orders:
        print(order)
        if not order_exists(order['order_id']):
            orderObject = Orders(instruments=order['tradingsymbol'], qty=order['quantity'],
                                 status=order['status'], avgTradedPrice=order['average_price'], instrumentsToken=order['instrument_token'],
                                 orderTimestamp=order['order_timestamp'], orderType=order[
                                     'order_type'], transactionType=order['transaction_type'],
                                 product=order['product'], orderId=order['order_id'])
            orderObject.save()
    return Orders.objects.all()


def total_pnl():
    total = Positions.objects.aggregate(TOTAL=Sum('pnl'))['TOTAL']
    if total:
        updatePNL(total)
        return round(total, 3)

# =========================
# Algo Core Logic Method
# =========================
# Steps for the logic


def CheckTradingTime():
    ist = pytz.timezone('Asia/Kolkata')
    current_dt = datetime.now(ist)
    market_start_time = current_dt.replace(
        hour=10, minute=0, second=0, microsecond=0)
    market_end_time = current_dt.replace(
        hour=15, minute=30, second=0, microsecond=0)

    # Get value from Settings
    settings = Preferences.objects.first()
    if settings:
        market_start_time = ist.localize(
            datetime.combine(current_dt, settings.time))

    if (current_dt >= market_start_time) and (current_dt <= market_end_time):
        return True
    return False


def coreLogic():  # A methond to check
    
    threading.Timer(0.5, coreLogic).start()
    checkTrade = CheckTradingTime()

    with coreLogicLock:
        if checkTrade:
            watchForAlgowatchlistBuySellLogic()
        watchForManualListBuySellLogic()

    getPositions()
    total_pnl()


def watchForAlgowatchlistBuySellLogic():
    
    # print("++++++++++++++++++++++++Algowatchlist Positions++++++++++++++++")
    algoArray = AlgoWatchlist.objects.all()
    # print(algoArray, "++++++++++++++++Algo Array Values=============")

    # Get value from Settings
    settings = Preferences.objects.all()
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
    for items in algoArray:  # Reliance
        if items.instruments in liveData:
            liveValues = liveData[items.instruments]
            # UBL : #then UBL(Upper band limit)) is 2448 (2% of 2400, 2400 + 48 = 2448)
            partValue = (ordp*liveValues['Open'])/100
            ubl = liveValues['Open'] + partValue
            # LBL : #then LBL(Lower band limit)) is 2352 (2% of 2400, 2400 - 48 = 2352)
            lbl = liveValues['Open'] - partValue
            # #SLHit: 0 #Counter for SL Hit for particualr script
            # print("Checking algo for " + items.instruments)
            # IF_Check if Algo is started and Not any positon open for that script
            if items.startAlgo and not items.openPostion:
                if ordtick:  # IF_ORD True check if open is in range
                    # IF_check CMP > OPEN and (CMP > LBL and CMP > UPL)
                    if (liveValues['LTP'] > liveValues['Open']) and (liveValues['LTP'] < ubl and liveValues['LTP'] > lbl):
                        print('SCRIPT QUANTITY=========================', 1)
                        logging.warning(
                            "Opening range is selected so only checking both ltp > Open and ltp in in range")
                        tradeInitiateWithSLTG(type="BUY", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                              ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=False)
                        AlgoWatchlist.objects.filter(instruments=items.instruments).update(qty=1)

                    # ELSE_#check CMP < OPEN and (CMP > LBL and CMP > UPL)
                    elif (liveValues['LTP'] < liveValues['Open']) and (liveValues['LTP'] < ubl and liveValues['LTP'] > lbl):
                        print('SCRIPT QUANTITY=========================', 2)
                        logging.warning(
                            "Opening range is selected so only checking both ltp < Open and ltp in in range")
                        tradeInitiateWithSLTG(type="SELL", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                              ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=False)
                        AlgoWatchlist.objects.filter(instruments=items.instruments).update(qty=1)
                else:  # ELSE_ORD False means do not check if open is in range
                    #if liveValues['LTP'] != liveValues['Open'] :
                        if liveValues['LTP'] > liveValues['Open']:  # IF_check CMP > OPEN
                            print('SCRIPT QUANTITY=========================', 3)
                            logging.warning(
                                "Opening range is not selected so only checking ltp > Open")
                            tradeInitiateWithSLTG(type="BUY", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                                ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=False)

                            AlgoWatchlist.objects.filter(instruments=items.instruments).update(qty=1)
                        elif liveValues['LTP'] < liveValues['Open']:  # ELSE_#check CMP < OPEN
                            print('SCRIPT QUANTITY=========================', 4)
                            logging.warning(
                                "Opening range is not selected so only checking ltp < Open")
                            tradeInitiateWithSLTG(type="SELL", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                                ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=False)
                            AlgoWatchlist.objects.filter(instruments=items.instruments).update(qty=1)
                    
            # ELSEIF_check if Algo is started and Position Open (Either Buy or Sell)
            elif items.startAlgo and items.openPostion:
                postions = Positions.objects.filter(
                    instruments=items.instruments)
                if postions:
                    potionObject = postions.values()[0]
                    setQty = abs(potionObject['qty'])
                    # IF_check if position is BUY and
                    if potionObject['positionType'] == "BUY":
                        if liveValues['LTP'] <= potionObject['slPrice']:
                            finalQty = 0
                            closeTrade = False
                            slCount = items.slHitCount + 1
                            if items.qty != setQty:
                                logging.warning("SELL:Take qty from Qty box Algo Sell=============== %s ", items.qty)
                                logging.warning("SELL:Take qty from Postion object Algo Sell===============%s ", setQty)
                                #setQty = items.qty
                            finalQty = setQty+(items.qty*setQty)
                            print('SCRIPT QUANTITY=========================', 5)
                            logging.warning(
                                "SELL:Double the qty box=============== %s", setQty)
                            tradeInitiateWithSLTG(type="SELL", scriptQty=finalQty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                                  ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=closeTrade)
                            AlgoWatchlist.objects.filter(instruments=items.instruments).update(slHitCount=slCount,qty=1)
                        elif liveValues['LTP'] >= potionObject['tgPrice']:  # IF CMP >= TG
                            print('SCRIPT QUANTITY=========================', 6)
                            tradeInitiateWithSLTG(type="SELL", scriptQty=setQty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                                  ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)
                        # else:
                        #     print("Position BUYALGO, No SL, No TG so continue")
                    # ELSE_check if positino is SELL
                    elif potionObject['positionType'] == "SELL":
                        if liveValues['LTP'] >= potionObject['slPrice']:  # if CMP >= SL
                            finalQty = 0
                            closeTrade = False
                            slCount = items.slHitCount + 1
                            if items.qty != setQty:
                                logging.warning(
                                    "BUY:Take qty from Qty box Algo Sell=============== %s ", items.qty)
                                logging.warning(
                                    "BUY:Take qty from Postion object Algo Sell===============%s ", setQty)
                                #setQty = items.qty
                            logging.warning(
                                "BUY:Double the qty box=============== %s", setQty)
                            finalQty = setQty+(items.qty*setQty)
                            print('SCRIPT QUANTITY=========================', 7)
                            tradeInitiateWithSLTG(type="BUY", scriptQty=finalQty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                                  ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId="", isCloseTrade=closeTrade)
                            
                            AlgoWatchlist.objects.filter(instruments=items.instruments).update(slHitCount=slCount,qty=1)
                        elif liveValues['LTP'] <= potionObject['tgPrice']:  # IF CMP <= TG
                            print('SCRIPT QUANTITY=========================', 8)
                            tradeInitiateWithSLTG(type="BUY", scriptQty=setQty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                                  ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)
                        # else:
                        #     print("Position SELLALGO, No SL, No TG so continue")
            # ELSE_check if algo is stopped and Position Open (Either Buy or Sell)
            elif not items.startAlgo and items.openPostion:
                postions = Positions.objects.filter(
                    instruments=items.instruments)
                if postions:
                    potionObject = postions.values()[0]
                    setQty = abs(potionObject['qty'])
                    print(
                        "Not SL ot TG achived but manuaaly - Close Postions and stop algo")
                    AlgoWatchlist.objects.filter(
                        instruments=items.instruments).update(openPostion=False)
                    if potionObject['positionType'] == "BUY":
                        print('SCRIPT QUANTITY=========================', 9)
                        tradeInitiateWithSLTG(type="SELL", scriptQty=setQty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                              ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)
                    if potionObject['positionType'] == "SELL":
                        print('SCRIPT QUANTITY=========================', 10)
                        tradeInitiateWithSLTG(type="BUY", scriptQty=setQty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                              ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)
            # else:
            #     print("Nothing to trade from Algo Watchlist for " + items.instruments)
        # else:
        #     print("Key not exist in live data")
    # print("No script found to trade")


def watchForManualListBuySellLogic():

    # print(liveData,"++++++++++++++++++++++++coming from watchformanual consumers")
    manualArray = ManualWatchlist.objects.all()
    settings = Preferences.objects.all()
    # TG : Get % value from settings
    tg = settings.values()[0]['target']
    # SL : Get % value from settings
    sl = settings.values()[0]['stoploss']

    for items in manualArray:  # Reliance

        # print("Checking manual for " + items.instruments)
        # print("Live Datas")
        # print(liveData)
        if items.instruments in liveData:
            liveValues = liveData[items.instruments]
            if items.startAlgo and not items.openPostion:
                if items.isBuyClicked:  # IF_Buy_Clicked then Place buy order no condition need to check
                    tradeInitiateWithSLTG(type="BUY", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                          orderId="", ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, isCloseTrade=False)
                    ManualWatchlist.objects.filter(instruments=items.instruments).update(qty=1)
                elif items.isSellClicked:
                    tradeInitiateWithSLTG(type="SELL", scriptQty=items.qty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                          orderId="", ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, isCloseTrade=False)
                    ManualWatchlist.objects.filter(instruments=items.instruments).update(qty=1)
                else:
                    print("Nothing to trade from Manual Watchlist")
            elif items.startAlgo and items.openPostion:

                postions = Positions.objects.filter(
                    instruments=items.instruments)
                if postions:
                    potionObject = postions.values()[0]
                    # print(potionObject)
                    setQty = abs(potionObject['qty'])
                    # IF_check if position is BUY and
                    if potionObject['positionType'] == "BUY":
                        if liveValues['LTP'] <= potionObject['slPrice']:
                            closeTrade = False
                            slCount = items.slHitCount + 1
                            logging.warning(
                                "MANUAL: BUY SL Hit=============================")
                            finalQty = 0
                            if items.qty != setQty:
                                logging.warning("SELL:Take qty from Qty box Algo Sell=============== %s ", items.qty)
                                logging.warning("SELL:Take qty from Postion object Algo Sell===============%s ", setQty)
                                #setQty = items.qty
                            finalQty = setQty+(items.qty*setQty)
                            print('SCRIPT QUANTITY=========================', 5)
                            logging.warning(
                                "SELL:Double the qty box=============== %s", setQty)
                            
                            tradeInitiateWithSLTG(type="SELL", scriptQty=finalQty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                                  ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId="", isCloseTrade=closeTrade)
                            ManualWatchlist.objects.filter(instruments=items.instruments).update(slHitCount=slCount,qty=1)
                        elif liveValues['LTP'] >= potionObject['tgPrice']:  # IF CMP >= TG
                            print(potionObject['tgPrice'])
                            print("Target Achived so Close Postions and stop algo")
                            tradeInitiateWithSLTG(type="SELL", scriptQty=setQty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                                  ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
                        # else:
                        #     print("Position BUYMANUAL, No SL, No TG so continue")
                    # ELSE_check if positino is SELL
                    elif potionObject['positionType'] == "SELL":
                        if liveValues['LTP'] >= potionObject['slPrice']:  # if CMP >= SL
                            closeTrade = False
                            slCount = items.slHitCount + 1
                            logging.warning(
                                "MANUAL: SELL SL Hit=============================")
                            
                            finalQty = 0
                            if items.qty != setQty:
                                logging.warning("SELL:Take qty from Qty box Algo Sell=============== %s ", items.qty)
                                logging.warning("SELL:Take qty from Postion object Algo Sell===============%s ", setQty)
                                #setQty = items.qty
                            finalQty = setQty+(items.qty*setQty)
                            print('SCRIPT QUANTITY=========================', 5)
                            logging.warning(
                                "SELL:Double the qty box=============== %s", setQty)

                            tradeInitiateWithSLTG(type="BUY", scriptQty=finalQty, exchangeType=items.exchangeType, sl=sl, tg=tg, orderId="",
                                                  ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, isCloseTrade=closeTrade)
                            ManualWatchlist.objects.filter(instruments=items.instruments).update(slHitCount=slCount,qty=1)
                        elif liveValues['LTP'] <= potionObject['tgPrice']:  # IF CMP <= TG
                            print(potionObject['tgPrice'])
                            print("Target achived so Close Postions and stop algo")
                            tradeInitiateWithSLTG(type="BUY", scriptQty=potionObject['qty'], exchangeType=items.exchangeType, sl=sl, tg=tg, ltp=liveValues[
                                                  'LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
                        # else:
                        #     print("Position SELLMANUAL, No SL, No TG so continue")
            elif not items.startAlgo and items.openPostion:
                print("Algo is stopped and postion is running so closing the trade")
                postions = Positions.objects.filter(
                    instruments=items.instruments)
                if postions:
                    potionObject = postions.values()[0]
                    setQty = abs(potionObject['qty'])
                    print("Not SL ot TG achived but manuaaly - Close Postions and stop algo")
                    if potionObject['positionType'] == "BUY":
                        tradeInitiateWithSLTG(type="SELL", scriptQty=setQty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                              ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
                    if potionObject['positionType'] == "SELL":
                        tradeInitiateWithSLTG(type="BUY", scriptQty=setQty, exchangeType=items.exchangeType, sl=sl, tg=tg,
                                              ltp=liveValues['LTP'], scriptCode=items.instruments, isFromAlgo=False, orderId=potionObject['orderId'], isCloseTrade=True)
            # else:
            #     print("Nothing to trade in Manual Watchlist")
        # else:
        #     print("Key not existing in live data, Wating for live data")

# =========================
# Algo Commonn Methods
# =========================


def scaleUpQty(request):
    script = request.POST['script']
    qty = request.POST['scriptQty']
    isFromAlgo = request.POST['isFromAlgoTest']
    print("Updated QTY ===========+++++++", script, qty, isFromAlgo)
    if isFromAlgo == "True":
        AlgoWatchlist.objects.filter(instruments=script).update(qty=qty)
    else:
        ManualWatchlist.objects.filter(instruments=script).update(qty=qty)
    return HttpResponse("success")


def scaleDownQty(request):
    script = request.POST['script']
    qty = request.POST['scriptQty']
    isFromAlgo = request.POST['isFromAlgoTest']
    print("Updated QTY ===========+++++++", script, qty)
    if isFromAlgo == "True":
        AlgoWatchlist.objects.filter(instruments=script).update(qty=qty)
    else:
        ManualWatchlist.objects.filter(instruments=script).update(qty=qty)
    return HttpResponse("success")


@csrf_exempt
def deleteInstrument(request):
    script = request.POST['script']
    flag = request.POST['flag']
    if flag == "ManualWatch":
        ManualWatchlist.objects.filter(instruments=script).delete()
    elif flag == "AlgoWatch":
        AlgoWatchlist.objects.filter(instruments=script).delete()

    instrumentObject = Instruments.objects.filter(
        tradingsymbol=script).values()
    instumentData = instrumentObject[0]
    updateSubscriberList(
        instumentData["instrument_token"], instumentData["tradingsymbol"], False)
    return HttpResponse("success")


@csrf_exempt
def addInstrument(request):
    print("Came from JS to Add Instrument ==============" +
          request.POST['script'])
    script = request.POST['script']
    flag = request.POST['flag']
    instrumentObject = Instruments.objects.filter(
        tradingsymbol=script).values()
    instumentData = instrumentObject[0]
    print(instumentData["instrument_token"])
    print(instumentData["tradingsymbol"])
    updateSubscriberList(
        instumentData["instrument_token"], instumentData["tradingsymbol"], True)
    if flag == "ManualWatch":
        instrumentObjectToManualWatchlistObject(instrumentObject)
        manualWatchObject = ManualWatchlist.objects.filter(
            instruments=script).values()
        return JsonResponse({"instrument": list(manualWatchObject)})
    elif flag == "AlgoWatch":
        instrumentObjectToAlgoWatchlistObject(instrumentObject)
        algoWatchObject = AlgoWatchlist.objects.filter(
            instruments=script).values()
        return JsonResponse({"instrument": list(algoWatchObject)})


def buySingle(request):  # For Manual watchlist
    print("Came from JS to buy single" + request.POST['script'])
    print("Came from JS to start" + request.POST['scriptQty'])
    ManualWatchlist.objects.filter(
        instruments=request.POST['script']).update(startAlgo=True , entryprice=0.0 ,  algoStartTime=datetime.utcnow())
    ManualWatchlist.objects.filter(
        instruments=request.POST['script']).update(positionType="BUY")
    ManualWatchlist.objects.filter(instruments=request.POST['script']).update(
        qty=int(request.POST['scriptQty']))
    ManualWatchlist.objects.filter(
        instruments=request.POST['script']).update(isBuyClicked=True)
    sleep(1)
    return HttpResponse("success")


def sellSingle(request):  # For Manual watchlist
    print("Came from JS to sell single" + request.POST['script'])
    print("Came from JS to start" + request.POST['scriptQty'])
    ManualWatchlist.objects.filter(
        instruments=request.POST['script']).update(startAlgo=True , entryprice=0.0 ,  algoStartTime=datetime.utcnow())
    ManualWatchlist.objects.filter(
        instruments=request.POST['script']).update(positionType="SELL")
    ManualWatchlist.objects.filter(instruments=request.POST['script']).update(
        qty=int(request.POST['scriptQty']))
    ManualWatchlist.objects.filter(
        instruments=request.POST['script']).update(isSellClicked=True)
    sleep(1)
    return HttpResponse("success")

from django.db import transaction

@csrf_exempt
def startSingle(request):  # For Algo watchlist
    # print(liveData,"++++++++++++++++++++++++coming from consumers")
    print("Came from JS to start " + request.POST['script'], request.POST['scriptQty'])

    AlgoWatchlist.objects.filter(instruments=request.POST['script']).update(entryprice=0.0 , slHitCount = 0, startAlgo=True, algoStartTime=datetime.utcnow(), qty=int(request.POST['scriptQty']))

    
    sleep(1)
    
    
    # transaction.commit()
    # obj.save()
    
    return HttpResponse("success")


def stopSingle(request):  # For Manual and Algo watchlist
    print("Came from JS to stop" + request.POST['script'])
    if request.POST['isFromAlgoTest'] == "true":
        print("Stop Single from Algowatchlist")
        AlgoWatchlist.objects.filter(
            instruments=request.POST['script']).update(startAlgo=False)
        AlgoWatchlist.objects.filter(instruments=request.POST['script']).update(
            qty=int(request.POST['scriptQty']))
    else:
        print("Stop Single from Manualwatchlist")
        ManualWatchlist.objects.filter(
            instruments=request.POST['script']).update(startAlgo=False)
        ManualWatchlist.objects.filter(
            instruments=request.POST['script']).update(isSellClicked=False)
        ManualWatchlist.objects.filter(
            instruments=request.POST['script']).update(isBuyClicked=False)
        ManualWatchlist.objects.filter(instruments=request.POST['script']).update(
            qty=int(request.POST['scriptQty']))
    sleep(1)
    return HttpResponse("success")

def stopSinglehalf(request):  # For Manual and Algo watchlist


    # print("++++++++++++++++++++++++Algowatchlist Positions++++++++++++++++")
    algoArray = AlgoWatchlist.objects.all()
    # print(algoArray, "++++++++++++++++Algo Array Values=============")

    # Get value from Settings
    settings = Preferences.objects.all()
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

    acriptttt = request.POST['script']

    if acriptttt in liveData:
        liveValues = liveData[acriptttt]
        # UBL : #then UBL(Upper band limit)) is 2448 (2% of 2400, 2400 + 48 = 2448)
        partValue = (ordp*liveValues['Open'])/100
        ubl = liveValues['Open'] + partValue
        # LBL : #then LBL(Lower band limit)) is 2352 (2% of 2400, 2400 - 48 = 2352)
        lbl = liveValues['Open'] - partValue

    postions = Positions.objects.filter(instruments=acriptttt)
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
        tradeInitiateWithSLTG(type="SELL", scriptQty=setQty, exchangeType='NSE', sl=sl, tg=tg,
                                ltp=liveValues['LTP'], scriptCode=acriptttt, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)
    if potionObject['positionType'] == "SELL":
        print(setQty,'SCRIPT QUANTITY=========================', 'SELL')
        tradeInitiateWithSLTG(type="BUY", scriptQty=setQty, exchangeType='NSE', sl=sl, tg=tg,
                                ltp=liveValues['LTP'], scriptCode=acriptttt, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)

    sleep(1)
    return HttpResponse("success")


def stopSinglehalf_halfAlgo_manual(request):  # For Manual and Algo watchlist


    # print("++++++++++++++++++++++++Algowatchlist Positions++++++++++++++++")
    algoArray = ManualWatchlist.objects.all()
    # print(algoArray, "++++++++++++++++Algo Array Values=============")

    # Get value from Settings
    settings = Preferences.objects.all()
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

    acriptttt = request.POST['script']

    if acriptttt in liveData:
        liveValues = liveData[acriptttt]
        # UBL : #then UBL(Upper band limit)) is 2448 (2% of 2400, 2400 + 48 = 2448)
        partValue = (ordp*liveValues['Open'])/100
        ubl = liveValues['Open'] + partValue
        # LBL : #then LBL(Lower band limit)) is 2352 (2% of 2400, 2400 - 48 = 2352)
        lbl = liveValues['Open'] - partValue

    postions = Positions.objects.filter(instruments=acriptttt)
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
        tradeInitiateWithSLTG(type="SELL", scriptQty=setQty, exchangeType='NSE', sl=sl, tg=tg,
                                ltp=liveValues['LTP'], scriptCode=acriptttt, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)
    if potionObject['positionType'] == "SELL":
        print(setQty,'SCRIPT QUANTITY=========================', 'SELL')
        tradeInitiateWithSLTG(type="BUY", scriptQty=setQty, exchangeType='NSE', sl=sl, tg=tg,
                                ltp=liveValues['LTP'], scriptCode=acriptttt, isFromAlgo=True, orderId=potionObject['orderId'], isCloseTrade=True)

    sleep(1)
    return HttpResponse("success")


def tradeInitiateWithSLTG(type, exchangeType, scriptQty, scriptCode, ltp, sl, tg, isFromAlgo, orderId, isCloseTrade):
    # type should be "BUY" or "SELL"
    # exchangeType should be "NFO" or "NSE"
    logging.warning("Trade Executed Start============")
    logging.warning("Type = %s", type)
    logging.warning("ExchangeType = %s", exchangeType)
    logging.warning("Qty = %s", scriptQty)
    logging.warning("Script Code = %s", scriptCode)
    logging.warning("LTP = %s", ltp)
    logging.warning("Stoploss = %s", sl)
    logging.warning("Target = %s", tg)
    logging.warning("is From Algo = %s", isFromAlgo)
    logging.warning("Order Id = %s", orderId)
    logging.warning("Is Trade Close = %s", isCloseTrade)
    logging.warning("Trade Executed Close============")
    # Place order (with ScriptQTY)
    try:

        orderId = ""
        orderId = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchangeType,
                                   tradingsymbol=scriptCode, transaction_type=type, quantity=abs(
                                       scriptQty),
                                   product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_MARKET, validity=kite.VALIDITY_DAY)

    except Exception as e:
        # logging.info("Order placement failed ")
        if isFromAlgo:
            AlgoWatchlist.objects.filter(
                instruments=scriptCode).update(openPostion=False)
            # AlgoWatchlist.objects.filter(instruments = scriptCode).update(startAlgo = False)
        else:
            ManualWatchlist.objects.filter(
                instruments=scriptCode).update(openPostion=False)
            # ManualWatchlist.objects.filter(instruments = scriptCode).update(startAlgo = False)

    else:
        if not isCloseTrade:

            logging.warning("Order places successfully=================")
            if isFromAlgo:
                logging.warning("Algo Open Position Updated=================")
                AlgoWatchlist.objects.filter(
                    instruments=scriptCode).update(openPostion=True)

                entryPrice11 = float(AlgoWatchlist.objects.filter(instruments=scriptCode).values()[0]["entryprice"])
                if entryPrice11==0.0:
                    AlgoWatchlist.objects.filter(instruments=scriptCode).update(entryprice=ltp)

            else:
                print("Manual Open Position Updated++++++++++++")
                ManualWatchlist.objects.filter(
                    instruments=scriptCode).update(openPostion=True)

                entryPrice11 = float(ManualWatchlist.objects.filter(instruments=scriptCode).values()[0]["entryprice"])
                if entryPrice11==0.0:
                    ManualWatchlist.objects.filter(instruments=scriptCode).update(entryprice=ltp)

            if position_exists(scriptCode):
                Positions.objects.filter(
                    instruments=scriptCode).update(qty=abs(scriptQty))
            getPositionAndUpdateModels(ltp, scriptCode, orderId, type)
        else:

            print("Order closed successfully=============================")
            if isFromAlgo:
                AlgoWatchlist.objects.filter(
                    instruments=scriptCode).update(openPostion=False)
            else:
                ManualWatchlist.objects.filter(
                    instruments=scriptCode).update(openPostion=False)
            if position_exists(scriptCode):
                Positions.objects.filter(instruments=scriptCode).update(qty=0)
        getPositions()
    #winsound.PlaySound('./playy.mp3', winsound.SND_FILENAME|winsound.SND_NOWAIT)
   
   
    # winsound.PlaySound("SystemQuestion", winsound.SND_NOWAIT)  
    #winsound.Beep(440, 500)

def getPositionAndUpdateModels(ltp, scriptCode, orderId, type):
    if type == "BUY":
        result = calculateSLTGPrice(ltp, type)
        # print(f"Modified SL Price ({scriptCode})= " + str(result[0]))
        # print(f"Modified TG Price ({scriptCode})= " + str(result[1]))
        # print(f"Modified LTP ({scriptCode})= " + str(ltp))
        if position_exists(scriptCode):
            Positions.objects.filter(instruments=scriptCode).update(
                slPrice=result[0], tgPrice=result[1], entryprice=ltp, orderId=orderId, positionType="BUY")
    else:
        result = calculateSLTGPrice(ltp, type)
        # print(f"Modified SL Price ({scriptCode})= " + str(result[0]))
        # print(f"Modified TG Price ({scriptCode})= " + str(result[1]))
        # print(f"Modified LTP ({scriptCode})= " + str(ltp))
        if position_exists(scriptCode):
            Positions.objects.filter(instruments=scriptCode).update(
                slPrice=result[0], tgPrice=result[1], entryprice=ltp, orderId=orderId, positionType="SELL")


def calculateSLTGPrice(ltp, type):
    settings = Preferences.objects.all()
    # TG : Get % value from settings
    tg = settings.values()[0]['target']
    # SL : Get % value from settings
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
        AlgoWatchlist.objects.filter(
            instruments=items.instruments).update(startAlgo=False)
        # AlgoWatchlist.objects.filter(instruments = items.instruments).update(qty = int(request.POST['scriptQty']))
    return redirect(request.META['HTTP_REFERER'])


def startAll(request):
    print("Came from JS to start All")
    algoArray = AlgoWatchlist.objects.all()
    print(len(algoArray))
    for items in algoArray:
        print("Starting for all items: ", items.instruments)
        AlgoWatchlist.objects.filter(
            instruments=items.instruments).update(startAlgo=True, algoStartTime=datetime.utcnow())
        AlgoWatchlist.objects.filter(instruments=items.instruments).update(qty=int(request.POST['scriptQty']))
    return redirect(request.META['HTTP_REFERER'])


def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

# while datetime.datetime.now().time() > datetime.time(9,14,00):
    # isIntrumentDownloaded = False
