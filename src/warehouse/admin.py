from django.contrib import admin
from .models import Item, ItemUnit, ItemType, Manufacturer


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "type", "manufacturer", "quantity", "market_value")
    list_filter = ("company", "type", "manufacturer")
    search_fields = ("name", "model", "description")


@admin.register(ItemType)
class ItemTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "company")
    list_filter = ("company",)
    search_fields = ("name",)


@admin.register(ItemUnit)
class ItemUnitAdmin(admin.ModelAdmin):
    list_display = ("item", "state")
    list_filter = ("state", "item__company")
    search_fields = ("item__name", "remark")


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ("name", "company")
    list_filter = ("company",)
    search_fields = ("name",)
