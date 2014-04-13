from django.contrib import admin
from models import Ship, ShipYard, ShipStock, Fleet, FleetShip

admin.site.register(Ship)
admin.site.register(ShipYard)
admin.site.register(ShipStock)
admin.site.register(Fleet)
admin.site.register(FleetShip)