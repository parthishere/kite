import asyncio
from datetime import datetime
from time import sleep
from channels.consumer import AsyncConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import sync_to_async
from .models import ManualWatchlist, AlgoWatchlist
from time import sleep
import json
from kiteconnect import KiteConnect, KiteTicker
from django.conf import settings
from playground.models import Instruments
from django.db.models import Q
import logging

# =========================
# Websocket Data Connection Methods
# =========================
# logger = logging.getLogger()
logging.basicConfig(filename='weberror.log', level=logging.DEBUG)
logger = logging.getLogger('spam')
subscriberlist = {}
defaultsubscriberlist = {256265: 'NIFTY 50', 260105: 'NIFTY BANK'}
liveData = {}
newPositionsdict = {}
updatedPNL = {}
# instrumentUpdate = Instruments.objects.filter(Q(tradingsymbol='ITC', exchange = 'NSE') | Q(tradingsymbol='HDFC', exchange = 'NSE') |  Q(tradingsymbol='RELIANCE', exchange = 'NSE') | Q(tradingsymbol='BPCL', exchange = 'NSE') | Q(tradingsymbol='ABB', exchange = 'NSE') | Q(tradingsymbol='IEX', exchange = 'NSE')).values()
# for instrumentObject in instrumentUpdate:
#     tokens = instrumentObject.get('instrument_token')
#     if not tokens in subscriberlist:
#         # print("Adding token to subscriber list")
#         subscriberlist[int(tokens)] = instrumentObject.get('tradingsymbol')


def updateSubscriberList(token, tradingSymbol, isSubscribe):
    if isSubscribe:
        subscriberlist[int(token)] = tradingSymbol
    else:
        if len(subscriberlist) > 0:
            try:
                subscriberlist.pop(int(token))
            except Exception as e:
                print(e)



def updatePostions(positionsdict):
    newPositionsdict["new"] = positionsdict


@sync_to_async
def getSlHits():
    data = {
        'ManualWatch': {},
        'AlgoWatch': {}
    }

    for instrument in AlgoWatchlist.objects.all():
        data['AlgoWatch'][instrument.instruments] = instrument.slHitCount

    for instrument in ManualWatchlist.objects.all():
        data['ManualWatch'][instrument.slHitCount] = instrument.slHitCount

    return data


def updatePNL(pnlValue):
    pnl_value = "+{}".format(round(pnlValue,2)) if pnlValue > 0 else round(pnlValue,2)
    # print("PNLValue = ",pnl_value)
    updatedPNL["pnl"] = str(pnl_value)
    # print(updatedPNL)


def startLiveConnection(token):
    kws = KiteTicker(api_key=settings.KITE_API_KEY, access_token=token)
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.connect(threaded=True)


def on_ticks(ws, ticks):
    # Callback to receive ticks.
    # Update subscribed instrument list
    subscriptionStatus(ws)

    liveData['default_instruments'] = default_instruments = {}
    for stock in ticks:
        # print(stock['instrument_token'])
        # print(list(subscriberlist.keys()))
        # print(subscriberlist[stock['instrument_token']])
        instrument_token = stock['instrument_token']
        # Put default subscribed instrument data in a separate field
        if instrument_token in defaultsubscriberlist:
            default_instruments[defaultsubscriberlist[instrument_token]] = {"Open": stock['ohlc']['open'],
                                                                            "Open": stock['ohlc']['open'],
                                                                            "High": stock['ohlc']['high'],
                                                                            "Low": stock['ohlc']['low'],
                                                                            "Close": stock['ohlc']['close'],
                                                                            "LTP": stock['last_price']}

        if instrument_token in subscriberlist:
            liveData[subscriberlist[instrument_token]] = {"Open": stock['ohlc']['open'],
                                                          "Open": stock['ohlc']['open'],
                                                          "High": stock['ohlc']['high'],
                                                          "Low": stock['ohlc']['low'],
                                                          "Close": stock['ohlc']['close'],
                                                          "LTP": stock['last_price']}

        # coreLogic(liveData)
        # print("Checking live data")
        # logging.warning('Live data in orders===== %s',stock['last_price'])
        #print(liveData, "+++++============++++++")

        #print(liveData)
        # manualArray = ManualWatchlist.objects.all()

        # print("HERE")
        # now = datetime.now()

        # dt_string = now.strftime("%H:%M:%S")
        # print("date and time =", dt_string)
        # for items in manualArray:
        #     if items.instruments in liveData:
        #         liveValues = liveData[items.instruments]
        #         print(liveValues['LTP'])

def AlgoWatchLogic(token, tradingSymbol, isSubscribe):
    if isSubscribe:
        subscriberlist[int(token)] = tradingSymbol
    else:
        if len(subscriberlist) > 0:
            try:
                subscriberlist.pop(int(token))
            except Exception as e:
                print(e)
                
def subscriptionStatus(ws: KiteTicker):
    instrument_tokens = list(defaultsubscriberlist.keys()
                             ) + list(subscriberlist.keys())
    ws.subscribe(instrument_tokens=instrument_tokens)
    ws.set_mode(mode=ws.MODE_FULL, instrument_tokens=instrument_tokens)


def on_connect(ws, response):
    logger.info('====== Connected to KiteTicker ======')
    subscriptionStatus(ws)


def on_close(ws: KiteTicker, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`
    subscriptionStatus(ws)
    ws.stop()


class MyAsyncConsumer(AsyncConsumer):

    async def websocket_connect(self, event):
        logger.info('WEBSOCKET CONNECTED=================================')
        logger.info("WEBSOCKET CONNECTED...........", event)
        # print("call file ***", event)
        await self.send({
            'type': 'websocket.accept'
        })
        # print(liveData, "______________________++++++++++live data 1")
        # counter = 0
        try:
            while True:
                valDict = {}
                # print(updatedPNL['pnl'],"______________________++++++++++pnl data 2")
                await asyncio.sleep(1)
                valDict["liveData"] = liveData
                valDict["position"] = newPositionsdict['new']
                valDict["totalpnl"] = updatedPNL.get('pnl')
                valDict['slHits'] = await getSlHits()
                # valDict['fetchALgoWatch'] = fetchAlgoWatch
                
                # if fetchAlgoWatch:
                #     fetchAlgoWatch = False
                # counter+=1
                # print(valDict)
                await self.send({
                    'type': 'websocket.send',
                    'text': json.dumps(valDict)
                })
        except Exception as e:
            print(e);
            # print(subscriberlist, "++++++++Subscriber list++++++++++")
            # sleep(1)
            # print("counter: ", counter)

    async def websocket_receive(self, event):
        print("Message received from client", event)
        print("The sent Message is: ", event['text'])
        # company_prices = compRanScriptGenerator()
        # await self.send({
        #     'type': 'websocket.send',
        #     'text': json.dumps(company_prices)
        # })

    async def websocket_disconnect(self, event):
        logger.info("WEBSOCKET DISCONNECTED=====", event)
        raise StopConsumer()
