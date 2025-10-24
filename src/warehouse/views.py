from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from .models import Item


@login_required
def home(request: HttpRequest) -> HttpResponse:
    items = Item.objects.all()
    return render(request, 'warehouse/pages/home.html', {
        'title': 'Início', 'items': items})


@login_required
def items(request: HttpRequest) -> HttpResponse:
    items = Item.objects.all()
    return render(request, 'warehouse/pages/items.html', {
        'title': 'Itens', 'items': items})
