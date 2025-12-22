from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from users.group_validation import is_in_group
from users import groups
from .forms import ItemForm
from .models import Item


@login_required
def home(request: HttpRequest) -> HttpResponse:
    items = Item.objects.all()
    if is_in_group(request.user, groups.MANAGER):
        return render(request, 'warehouse/pages/home.html',
                      {'title': 'Início', 'items': items})
    elif is_in_group(request.user, groups.DEFAULT):
        return render(request, 'warehouse/pages/items.html',
                      {'title': 'Itens', 'items': items})
    else:
        return render(request, 'warehouse/pages/items.html',
                      {'title': 'Itens', 'items': items})


@login_required
def items(request: HttpRequest) -> HttpResponse:
    items = Item.objects.all()
    return render(request, 'warehouse/pages/items.html', {
        'title': 'Itens', 'items': items})


@login_required
def create_item(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('warehouse:items')

    form = ItemForm()
    return render(request, 'warehouse/pages/create_item.html', {
        'title': 'Criar Item', 'form': form})
