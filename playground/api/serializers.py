from ..models import *
from rest_framework import serializers 

class PreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model=Preferences
        field = "__all__"
        
class AlgoWatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model=Preferences
        field = "__all__"
        
class InstrumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Preferences
        field = "__all__"

# For algowatch API
class AlgoWatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlgoWatchlist
        field = "__all__"

# For instrument API
class InstrumentSearializer(serializers.ModelSerializer):
    class Meta:
        model = Instruments
        field = "__all__"

# For orderlist API
class OrderSerializer(serializers.ModelSerializer):
    time = serializers.CharField(source = 'orderTimestamp')
    type = serializers.CharField(source = 'transactionType')
    price = serializers.FloatField(source ='avgTradedPrice')
    class Meta:
        model = Orders
        fields = ('id','time','orderType','type','instruments','qty','status','price')