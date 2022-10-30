import imp
import logging
from multiprocessing import context
from pickle import FALSE, TRUE
from urllib import response
from django.shortcuts import render, redirect
from django.http import HttpResponse
from playground import kiteconnect, constants
from playground.models import Preferences, Intruments
from django.contrib import messages
from kiteconnect import KiteConnect
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key=constants.KITE_API_KEY)

# Create your views here.

def index(request):
    return render(request, 'index.html')

def loginUser(request):
    if request.method == 'GET':
        if request.GET['request_token'] != "":
            data = kite.generate_session(request.GET['request_token'], api_secret=constants.KITE_API_SECRETE)
            kite.set_access_token(data["access_token"])
            return redirect("/algowatch")
        messages.error(request, 'Authentication Failed! Please login again')
            

def algowatch(request):
    if kite.access_token is None:
        return redirect("/")
    # for item in kite.instruments():
    #         print(item)
    #         refreshWatchlist = FALSE
    return render(request, 'algowatch.html', {'name': kite.access_token})

def manualwatch(request):
    if kite.access_token is None:
        return redirect("/")
    return render(request, 'manualwatch.html', {'name': 'Manual Watch'})

def settings(request):
    if kite.access_token is None:
        return redirect("/")

    if request.method == "POST":
        time = request.POST.get('time')
        stoploss = request.POST.get('stoploss')
        target = request.POST.get('target')
        scaleupqty = request.POST.get('scaleupqty')
        scaledownqty = request.POST.get('scaledownqty')
        openingrange = request.POST.get('openingrange')
        openingrangebox = request.POST.get('openingrangebox')
        settings = Preferences(time=time, stoploss=stoploss, target=target, scaleupqty=scaleupqty, scaledownqty=scaledownqty, openingrange=openingrange)
        settings.save()
        messages.success(request, 'Preference updated successfully!')
    return render(request, 'settings.html', {'name': 'Settings'})


def logoutUser(request):
    kite.invalidate_access_token()
    return redirect("/")

def username_exists(username):
    return User.objects.filter(username=username).exists()