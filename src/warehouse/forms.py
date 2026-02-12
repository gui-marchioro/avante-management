from django import forms
from .models import Item
from companies.models import Company


class ItemForm(forms.ModelForm):  # type: ignore
    def __init__(self, *args, company: Company | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        self.fields["type"].queryset = self.fields["type"].queryset.filter(
            company=company)
        self.fields["manufacturer"].queryset = self.fields["manufacturer"].queryset.filter(
            company=company)

    class Meta:
        model = Item
        fields = ['name', 'type', 'manufacturer', 'model',
                  'quantity', 'market_value', 'description']
