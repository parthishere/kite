from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

def homelogin(request):
    return render(request, 'hello.html', {'name': 'Hardik'})

def algowatch(request):
    return render(request, 'hello.html', {'name': 'Algowatch'})

def manualwatch(request):
    return render(request, 'hello.html', {'name': 'Manual Watch'})

def settings(request):
    return render(request, 'hello.html', {'name': 'Settings'})