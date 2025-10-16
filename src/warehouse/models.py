from enum import Enum
from django.db import models


class ItemType(Enum):
    PLC = "plc"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    HMI = "hmi"
    PLC_EXPANSION = "plc_expansion"


class ItemState(Enum):
    NEW = "new"
    USED = "used"
    DAMAGED = "damaged"
    SOLD = "sold"


class Manufacturer(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=[
                            (tag.value, tag.value) for tag in ItemType])
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)
    model = models.CharField(max_length=100)
    quantity = models.IntegerField()
    market_value = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class ItemUnit(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=[
                             (tag.value, tag.value) for tag in ItemState])
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.item.name}"
