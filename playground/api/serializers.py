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