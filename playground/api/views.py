from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from kiteconnect import KiteConnect
from django.conf import settings
import threading
import logging
from ..views import coreLogic,login_in_zerodha
import pyotp

kite = KiteConnect(api_key=settings.KITE_API_KEY)

coreLogicLock = threading.Lock()
coreRunning = False

kite = KiteConnect(api_key=settings.KITE_API_KEY)

@api_view(["POST"])
def login_view(request):    
        if 'request_token' in request.POST and request.POST.get('request_token'):
            data = kite.generate_session(
                request.POST['request_token'], api_secret=settings.KITE_API_SECRET)
            kite.set_access_token(data["access_token"])
            coreLogic()
            return Response({'Data':"good"})    

@api_view(['GET'])
def login_with_zerodha(request):            
        topt = pyotp.TOTP('ZF3MONJ23XF34ESGSGRXOKR6RGTRQLXN')
        toptKey = topt.now()        
        kite = login_in_zerodha(settings.KITE_API_KEY, settings.KITE_API_SECRET, 'LN7447', 'zzzzaaaa', toptKey)
        profile = kite.profile()
        print(profile)
        return ("success")