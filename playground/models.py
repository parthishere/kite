from email.policy import default
from operator import mod
from django.db import models

# Create your models here.
class Preferences(models.Model):
    time = models.IntegerField(default = 10)
    stoploss = models.FloatField(default = 0.2)
    target = models.FloatField(default = 1.0)
    scaleupqty = models.IntegerField(default = 1, null=True)
    scaledownqty = models.IntegerField(default = 1, null=True)
    openingrange = models.FloatField(default = 10.0, null=True)
    openingrangebox = models.BooleanField(default=False, null=True)

class AlgoWatchlist(models.Model):
    instruments = models.CharField(max_length = 100)
    instrumentsToken = models.CharField(max_length = 100, default = "1111")
    entryprice = models.FloatField(default = 0.0)
    lastTradedPrice = models.FloatField(default = 0.0)
    qty = models.IntegerField(default = 1)
    scaleup = models.IntegerField(default = 1)
    scaledown = models.IntegerField(default = 1)
    startAlgo = models.BooleanField(default=False, null=True)
    openPostion = models.BooleanField(default=False, null=True)
    exchangeType = models.CharField(max_length = 100, default = "NFO")
    segment = models.CharField(max_length = 100, default = "NFO-FUT")
    instrumentType = models.CharField(max_length = 100, default = "CE")
    slHitCount = models.IntegerField(default = 1)


class ManualWatchlist(models.Model):
    instruments = models.CharField(max_length = 100)
    instrumentsToken = models.CharField(max_length = 100, default = "1111")
    entryprice = models.FloatField(default = 0.0)
    lastTradedPrice = models.FloatField(default = 0.0)
    qty = models.IntegerField(default = 1)
    scaleup = models.IntegerField(default = 1)
    scaledown = models.IntegerField(default = 1)
    startAlgo = models.BooleanField(default=False, null=True)
    openPostion = models.BooleanField(default=False, null=True)
    positionType = models.CharField(max_length = 100, default = "BUY")
    exchangeType = models.CharField(max_length = 100, default = "NFO")
    segment = models.CharField(max_length = 100, default = "NFO-FUT")
    instrumentType = models.CharField(max_length = 100, default = "CE")
    isBuyClicked = models.BooleanField(default=False, null=False)
    isSellClicked = models.BooleanField(default=False, null=False)
    slHitCount = models.IntegerField(default = 1)


class Positions(models.Model):
    instruments = models.CharField(max_length = 100)
    instrumentsToken = models.CharField(max_length = 100, default = "1111")
    qty = models.IntegerField(default = 1)
    entryprice = models.FloatField(default = 0.0)
    avgTradedPrice = models.FloatField(default = 0.0)
    lastTradedPrice = models.FloatField(default = 0.0)
    pnl = models.FloatField(default = 0.0)
    unrealised = models.FloatField(default = 0.0)
    realised = models.FloatField(default = 0.0)
    startAlgo = models.BooleanField(default=False, null=True)
    slPrice = models.FloatField(default = 0.0)
    tgPrice = models.FloatField(default = 0.0)
    orderId = models.CharField(max_length = 100, default = "1111")
    positionType = models.CharField(max_length = 100, default = "")

class Orders(models.Model):
    instruments = models.CharField(max_length = 100)
    instrumentsToken = models.CharField(max_length = 100, default = "1111")
    status = models.CharField(max_length = 100, default = "COMPLETE")
    statusMessage = models.CharField(max_length = 100, default = "COMPLETE")
    qty = models.IntegerField(default = 1)
    orderId = models.CharField(max_length = 100, default = "1111")
    orderTimestamp = models.CharField(max_length = 100, default = "2021-05-31 09:18:57")
    orderType = models.CharField(max_length = 100, default = "LIMIT")
    transactionType = models.CharField(max_length = 100, default = "BUY")
    avgTradedPrice = models.FloatField(default = 0.0)
    product = models.CharField(max_length = 100, default = "MIS")


class Instruments(models.Model):
    instrument_token = models.CharField(max_length = 100)
    exchange_token = models.CharField(max_length = 100)
    tradingsymbol = models.CharField(max_length = 100)
    name = models.CharField(max_length = 100)
    last_price = models.FloatField(default = 0.0)
    expiry = models.CharField(max_length = 100)
    tick_size = models.FloatField(default = 0.0)
    strike = models.FloatField(default = 0.0)
    lot_size = models.IntegerField(default = 1)
    instrument_type = models.CharField(max_length = 100)
    segment = models.CharField(max_length = 100)
    exchange = models.CharField(max_length = 100)

