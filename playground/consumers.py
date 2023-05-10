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
from playground import constants_old
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
            subscriberlist.pop(int(token), None)


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
    print(updatedPNL)


def startLiveConnection(token):
    kws = KiteTicker(api_key=constants_old.KITE_API_KEY, access_token=token)
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
    ws.stop()


class MyAsyncConsumer(AsyncConsumer):

    async def websocket_connect(self, event):
        logger.info('WEBSOCKET CONNECTED=================================')
        logger.info("WEBSOCKET CONNECTED...........", event)
        print("call file ***", event)
        await self.send({
            'type': 'websocket.accept'
        })
        # print(liveData, "______________________++++++++++live data 1")
        # counter = 0
        try:
            while True:
                valDict = {}
                # print(updatedPNL['pnl'],"______________________++++++++++pnl data 2")
                await asyncio.sleep(0.5)
                valDict["liveData"] = liveData
                valDict["position"] = newPositionsdict['new']
                valDict["totalpnl"] = updatedPNL.get('pnl')
                valDict['slHits'] = await getSlHits()
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


"""
{
    "liveData": {
        "default_instruments": {
            "NIFTY 50": {
                "Open": 18117.3,
                "High": 18216.95,
                "Low": 18104.9,
                "Close": 18255.8,
                "LTP": 18132.85
            },
            "NIFTY BANK": {
                "Open": 43110.65,
                "High": 43588.0,
                "Low": 43035.35,
                "Close": 43685.45,
                "LTP": 43237.75
            }
        },
        "UBL": {
            "Open": 1380.0,
            "High": 1420.0,
            "Low": 1372.3,
            "Close": 1430.15,
            "LTP": 1410.05
        },
        "NYKAA": {
            "Open": 129.0,
            "High": 131.7,
            "Low": 127.95,
            "Close": 128.6,
            "LTP": 130.85
        },
        "WABAG": {
            "Open": 415.0,
            "High": 415.0,
            "Low": 403.5,
            "Close": 411.5,
            "LTP": 404.5
        }
    },
    "position": {
        "net": [
            {
                "tradingsymbol": "NYKAA",
                "exchange": "NSE",
                "instrument_token": 1675521,
                "product": "MIS",
                "quantity": -1,
                "overnight_quantity": 0,
                "multiplier": 1,
                "average_price": -0.05,
                "close_price": 0,
                "last_price": 0.19098548510313215,
                "value": 130.8,
                "pnl": -0.05,
                "m2m": 0.10000000000002274,
                "unrealised": 0.10000000000002274,
                "realised": 0,
                "buy_quantity": 1,
                "buy_price": 131,
                "buy_value": 131,
                "buy_m2m": 131,
                "sell_quantity": 2,
                "sell_price": 130.9,
                "sell_value": 261.8,
                "sell_m2m": 261.8,
                "day_buy_quantity": 1,
                "day_buy_price": 131,
                "day_buy_value": 131,
                "day_sell_quantity": 2,
                "day_sell_price": 130.9,
                "day_sell_value": 261.8
            },
            {
                "tradingsymbol": "UBL",
                "exchange": "NSE",
                "instrument_token": 4278529,
                "product": "MIS",
                "quantity": 0,
                "overnight_quantity": 0,
                "multiplier": 1,
                "average_price": -2.2657894736842104,
                "close_price": 0,
                "last_price": -0.8024634976969941,
                "value": -43.04999999999927,
                "pnl": -43.05,
                "m2m": -43.04999999999927,
                "unrealised": -43.04999999999927,
                "realised": 0,
                "buy_quantity": 19,
                "buy_price": 1411.7710526315789,
                "buy_value": 26823.649999999998,
                "buy_m2m": 26823.649999999998,
                "sell_quantity": 19,
                "sell_price": 1409.5052631578947,
                "sell_value": 26780.6,
                "sell_m2m": 26780.6,
                "day_buy_quantity": 19,
                "day_buy_price": 1411.7710526315789,
                "day_buy_value": 26823.649999999998,
                "day_sell_quantity": 19,
                "day_sell_price": 1409.5052631578947,
                "day_sell_value": 26780.6
            },
            {
                "tradingsymbol": "WABAG",
                "exchange": "NSE",
                "instrument_token": 5168129,
                "product": "MIS",
                "quantity": 0,
                "overnight_quantity": 0,
                "multiplier": 1,
                "average_price": -0.93,
                "close_price": 0,
                "last_price": -1.1472982975573733,
                "value": -4.650000000000091,
                "pnl": -4.65,
                "m2m": -4.650000000000091,
                "unrealised": -4.650000000000091,
                "realised": 0,
                "buy_quantity": 5,
                "buy_price": 405.3,
                "buy_value": 2026.5,
                "buy_m2m": 2026.5,
                "sell_quantity": 5,
                "sell_price": 404.37,
                "sell_value": 2021.85,
                "sell_m2m": 2021.85,
                "day_buy_quantity": 5,
                "day_buy_price": 405.3,
                "day_buy_value": 2026.5,
                "day_sell_quantity": 5,
                "day_sell_price": 404.37,
                "day_sell_value": 2021.85
            }
        ],
        "day": [
            {
                "tradingsymbol": "NYKAA",
                "exchange": "NSE",
                "instrument_token": 1675521,
                "product": "MIS",
                "quantity": -1,
                "overnight_quantity": 0,
                "multiplier": 1,
                "average_price": 130.9,
                "close_price": 0,
                "last_price": 130.7,
                "value": 130.8,
                "pnl": 0.10000000000002274,
                "m2m": 0.10000000000002274,
                "unrealised": 0.10000000000002274,
                "realised": 0,
                "buy_quantity": 1,
                "buy_price": 131,
                "buy_value": 131,
                "buy_m2m": 131,
                "sell_quantity": 2,
                "sell_price": 130.9,
                "sell_value": 261.8,
                "sell_m2m": 261.8,
                "day_buy_quantity": 1,
                "day_buy_price": 131,
                "day_buy_value": 131,
                "day_sell_quantity": 2,
                "day_sell_price": 130.9,
                "day_sell_value": 261.8
            },
            {
                "tradingsymbol": "UBL",
                "exchange": "NSE",
                "instrument_token": 4278529,
                "product": "MIS",
                "quantity": 0,
                "overnight_quantity": 0,
                "multiplier": 1,
                "average_price": 0,
                "close_price": 0,
                "last_price": 1409.85,
                "value": -43.04999999999927,
                "pnl": -43.04999999999927,
                "m2m": -43.04999999999927,
                "unrealised": -43.04999999999927,
                "realised": 0,
                "buy_quantity": 19,
                "buy_price": 1411.7710526315789,
                "buy_value": 26823.649999999998,
                "buy_m2m": 26823.649999999998,
                "sell_quantity": 19,
                "sell_price": 1409.5052631578947,
                "sell_value": 26780.6,
                "sell_m2m": 26780.6,
                "day_buy_quantity": 19,
                "day_buy_price": 1411.7710526315789,
                "day_buy_value": 26823.649999999998,
                "day_sell_quantity": 19,
                "day_sell_price": 1409.5052631578947,
                "day_sell_value": 26780.6
            },
            {
                "tradingsymbol": "WABAG",
                "exchange": "NSE",
                "instrument_token": 5168129,
                "product": "MIS",
                "quantity": 0,
                "overnight_quantity": 0,
                "multiplier": 1,
                "average_price": 0,
                "close_price": 0,
                "last_price": 404.7,
                "value": -4.650000000000091,
                "pnl": -4.650000000000091,
                "m2m": -4.650000000000091,
                "unrealised": -4.650000000000091,
                "realised": 0,
                "buy_quantity": 5,
                "buy_price": 405.3,
                "buy_value": 2026.5,
                "buy_m2m": 2026.5,
                "sell_quantity": 5,
                "sell_price": 404.37,
                "sell_value": 2021.85,
                "sell_m2m": 2021.85,
                "day_buy_quantity": 5,
                "day_buy_price": 405.3,
                "day_buy_value": 2026.5,
                "day_sell_quantity": 5,
                "day_sell_price": 404.37,
                "day_sell_value": 2021.85
            }
        ]
    },
    "totalpnl": "-47.75",
    "slHits": {
        "ManualWatch": {},
        "AlgoWatch": {
            "NYKAA": 1,
            "UBL": 8,
            "WABAG": 4
        }
    }
}

"""