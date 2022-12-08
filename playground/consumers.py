import asyncio
from time import sleep
from channels.consumer import AsyncConsumer
from channels.exceptions import StopConsumer
from time import sleep
import json
from kiteconnect import KiteConnect, KiteTicker
from playground import kiteconnect, constants
from playground.models import Instruments
from django.db.models import Q
import logging
#=========================
## Websocket Data Connection Methods
#=========================
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

subscriberlist = {5633: "ACC"}
liveData = {}
newPositionsdict = {}
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
            subscriberlist.pop(int(token))


def updatePostions(positionsdict):
    newPositionsdict["new"] = positionsdict



def startLiveConnection(token):

    logger.info("Starting live connecton with zerodha")
    logger.info("Starting live connecton with zerodha")

    logger.info("Starting live connecton with zerodha key + ", constants.KITE_API_KEY)
    logger.info("Starting live connecton with zerodha access token+ ", token)
    kws = KiteTicker(api_key=constants.KITE_API_KEY, access_token=token)
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.connect(threaded=True)

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    # logging.debug("Ticks: {}".format(ticks))
    subscriptionStatus(ws)

    for stock in ticks:
        # print(stock['instrument_token'])
        # print(list(subscriberlist.keys()))
        # print(subscriberlist[stock['instrument_token']])
        liveData[subscriberlist[stock['instrument_token']]] = {"Open": stock['ohlc']['open'],
            "Open": stock['ohlc']['open'],
            "High": stock['ohlc']['high'],
            "Low": stock['ohlc']['low'],
            "Close": stock['ohlc']['close'],
            "LTP": stock['last_price']}
        # coreLogic(liveData)
        # print("Checking live data")
        # logger.warning("Live data in orders=====",liveData)
        # print(liveData, "+++++============++++++")

def subscriptionStatus(ws):

    # print(subscriberlist, "Subscription Status ====================")
    ws.subscribe(list(subscriberlist.keys()))
    ws.set_mode(ws.MODE_FULL, list(subscriberlist.keys()))

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    # ws.subscribe([3329, 134657, 340481, 56321, 424961, 738561])
    # print("Starting new connection with Subscriber list")
    # print(list(subscriberlist.keys()))
    logger.warning("On connect of kite called=====",list(subscriberlist.keys()))
    ws.subscribe(list(subscriberlist.keys()))
    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, list(subscriberlist.keys()))

def on_close(ws, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()


class MyAsyncConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        logger.warning('WEBSOCKET CONNECTED=================================')
        print("WEBSOCKET CONNECTED...........",event)
        await self.send({
            'type':'websocket.accept'
        })
        # print(liveData,"______________________++++++++++liev data 1")
        # counter = 0
        while True:
            valDict = {}
            # print(liveData,"______________________++++++++++liev data 2")
            await asyncio.sleep(1)
            valDict["liveData"] = liveData
            valDict["position"] = newPositionsdict['new']
            # counter+=1
            await self.send({
                'type':'websocket.send',
                'text': json.dumps(valDict)
            })
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
        logger.warning("WEBSOCKET DISCONNECTED=====",event)
        print("WEBSOCKET DISCONNECTED////////////////////",event)
        raise StopConsumer()


