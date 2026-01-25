from django.contrib import admin
from .models import (Article, Bill, BillVersion, Event, 
                     MonitoredCommission, MonitoredMeasure, NewsPreset,
                     NewsSource, SystemSettings, UserProfile)

admin.site.register(Bill)
admin.site.register(BillVersion)
admin.site.register(Article)
admin.site.register(NewsSource)
admin.site.register(Event)
admin.site.register(NewsPreset)
admin.site.register(MonitoredMeasure)
admin.site.register(MonitoredCommission)
admin.site.register(SystemSettings)
admin.site.register(UserProfile)