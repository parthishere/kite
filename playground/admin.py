from django.contrib import admin
from playground.models import Preferences, DateTimeCheck, AlgoWatchlist, ManualWatchlist, Positions, Orders, Instruments

# Register your models here.
admin.site.register(Preferences)
admin.site.register(DateTimeCheck)
admin.site.register(AlgoWatchlist)
admin.site.register(ManualWatchlist)
admin.site.register(Positions)
admin.site.register(Orders)
admin.site.register(Instruments)