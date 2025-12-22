from django import forms
from .models import Item


class ItemForm(forms.ModelForm):  # type: ignore
    class Meta:
        model = Item
        fields = ['name', 'type', 'manufacturer', 'model',
                  'quantity', 'market_value', 'description']
