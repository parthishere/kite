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
    entryprice = models.FloatField(default = 0.0)
    lastTradedPrice = models.FloatField(default = 0.0)
    qty = models.IntegerField(default = 1)
    scaleup = models.IntegerField(default = 1)
    scaledown = models.IntegerField(default = 1)
    startAlgo = models.BooleanField(default=False, null=True)


class ManualWatchlist(models.Model):
    instruments = models.CharField(max_length = 100)
    entryprice = models.FloatField(default = 0.0)
    lastTradedPrice = models.FloatField(default = 0.0)
    qty = models.IntegerField(default = 1)
    scaleup = models.IntegerField(default = 1)
    scaledown = models.IntegerField(default = 1)
    startAlgo = models.BooleanField(default=False, null=True)


class Positions(models.Model):
    instruments = models.CharField(max_length = 100)
    qty = models.IntegerField(default = 1)
    entryprice = models.FloatField(default = 0.0)
    avgTradedPrice = models.FloatField(default = 0.0)
    lastTradedPrice = models.FloatField(default = 0.0)
    pnl = models.FloatField(default = 0.0)
    unrealised = models.FloatField(default = 0.0)
    realised = models.FloatField(default = 0.0)
    startAlgo = models.BooleanField(default=False, null=True)


class Intruments(models.Model):
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

