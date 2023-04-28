from ..models import *
from rest_framework import serializers 

class PreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model=Preferences
        fields = "__all__"
        
class AlgoWatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model=AlgoWatchlist
        fields = "__all__"
        
class ManualWatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model=ManualWatchlist
        fields = "__all__"
        
class InstrumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Instruments
        fields = "__all__"


class SearchInstrumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Instruments
        fields = ["instrument_token","tradingsymbol"]

# For orderlist API
class OrderSerializer(serializers.ModelSerializer):
    # time = serializers.CharField(source = 'orderTimestamp')
    # type = serializers.CharField(source = 'transactionType')
    # price = serializers.FloatField(source ='avgTradedPrice')
    class Meta:
        model = Orders
        fields = "__all__"

class PositionsSerializer(serializers.ModelSerializer):
    type=serializers.CharField(source ='positionType')
    entry=serializers.CharField(source ='entryprice')
    ltp=serializers.CharField(source ='lastTradedPrice')
    average=serializers.CharField(source ='avgTradedPrice')
    exit=serializers.CharField(source ='avgTradedPrice')
    actions=serializers.CharField(source ='startAlgo')
    # per = serializers.SerializerMethodField()

    # def get_per(self,obj):
    #     ltp = float(obj.lastTradedPrice)
    #     entry = float(obj.entryprice)
    #     try:
    #         return "{:.2f} %".format((ltp - entry) / entry * 100)
    #     except Exception as e:
    #         return str(e)
    class Meta:
        model = Positions
        fields = ("id","instruments","type","qty","entry","ltp","average","exit","actions","pnl","per")