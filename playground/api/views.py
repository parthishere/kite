from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from kiteconnect import KiteConnect
from django.conf import settings
import threading
from ..views import coreLogic

kite = KiteConnect(api_key=settings.KITE_API_KEY)

coreLogicLock = threading.Lock()
coreRunning = False

kite = KiteConnect(api_key=settings.KITE_API_KEY)

@api_view(["POST", "GET"])
def login_view(request):
    # if request.medthod == "POST":
    
    if request.method == 'GET':
        if request.GET['request_token'] != "":
            data = kite.generate_session(
                request.GET['request_token'], api_secret=settings.KITE_API_SECRET)
            kite.set_access_token(data["access_token"])
            coreLogic()
            return Response({'Data':"good"})


    return Response({"Data":"data"})