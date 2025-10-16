from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from .models import Item


def home(request: HttpRequest) -> HttpResponse:
    items = Item.objects.all()
    return render(request, 'warehouse/pages/home.html', {
        'title': 'Início', 'items': items})
