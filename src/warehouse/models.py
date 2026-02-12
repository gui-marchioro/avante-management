from enum import Enum
from django.db import models
from companies.models import Company


class ItemState(Enum):
    NEW = "new"
    USED = "used"
    DAMAGED = "damaged"
    SOLD = "sold"


class ItemType(models.Model):
    name = models.CharField(max_length=50)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="item_types",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_item_type_name_per_company",
            )
        ]

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    name = models.CharField(max_length=100)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="manufacturers",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_manufacturer_name_per_company",
            )
        ]

    def __str__(self):
        return self.name


class Item(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=100)
    type = models.ForeignKey(ItemType, on_delete=models.CASCADE)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)
    model = models.CharField(max_length=100)
    quantity = models.IntegerField()
    market_value = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    class Meta:
        permissions = [
            ("view_financial_dashboard", "Can view warehouse financial dashboard"),
        ]

    def __str__(self):
        return self.name


class ItemUnit(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=[
                             (tag.value, tag.value) for tag in ItemState])
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.item.name}"
