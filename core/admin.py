from django.contrib import admin
from .models import Bill, BillVersion, Article, NewsSource, Event, NewsPreset, MonitoredMeasure, MonitoredCommission, Keyword

# Esto hace que aparezcan las tablas en el panel
admin.site.register(Bill)
admin.site.register(BillVersion)
admin.site.register(Article)
admin.site.register(NewsSource)
admin.site.register(Event)

# Configuración extra
admin.site.register(NewsPreset)
admin.site.register(MonitoredMeasure)
admin.site.register(MonitoredCommission)
admin.site.register(Keyword)