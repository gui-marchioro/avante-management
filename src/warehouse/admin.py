from django.contrib import admin
from .models import Item, ItemUnit, Manufacturer


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    ...


@admin.register(ItemUnit)
class ItemUnitAdmin(admin.ModelAdmin):
    ...


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    ...
