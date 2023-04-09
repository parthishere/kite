from rest_framework.decorators import api_view
from rest_framework.response import Response    
from django.shortcuts import render, redirect
from kiteconnect import KiteConnect
from django.conf import settings
import threading
import logging
from ..views import coreLogic,login_in_zerodha
import pyotp
from .. import models
from . import serializers

kite = KiteConnect(api_key=settings.KITE_API_KEY)

coreLogicLock = threading.Lock()
coreRunning = False

kite = KiteConnect(api_key=settings.KITE_API_KEY)

@api_view(["GET"])
def login_view(request):    
        if 'request_token' in request.GET and request.GET.get('request_token'):
            data = kite.generate_session(
                request.GET['request_token'], api_secret=settings.KITE_API_SECRET)
            kite.set_access_token(data["access_token"])
            coreLogic()
            return Response({'Data':"good"})    

@api_view(['GET'])
def algowatch(request):        
        algowatchlist = models.AlgoWatchlist.objects.all()
        for obj in algowatchlist:
               print(obj)
        return Response("No Response")
       
@api_view(['GET'])
def OrdersApi(reqeust):
       orders_qs = models.Orders.objects.all()
       order_json = serializers.OrderSerializer(orders_qs,many=True).data
       return Response(order_json)

@api_view(['GET'])
def PositionsApi(reqeust):
       positions_qs = models.Positions.objects.all()
       positions_json = serializers.PositionsSerializer(positions_qs,many=True).data
       return Response(positions_json)