from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from .forms import ItemForm
from .models import Item


@login_required
def home(request: HttpRequest) -> HttpResponse:
    items = Item.objects.all()
    if request.user.has_perm('warehouse.view_financial_dashboard'):
        return render(request, 'warehouse/pages/home.html',
                      {'title': 'Início', 'items': items})
    else:
        return redirect('warehouse:items')


@login_required
@permission_required('warehouse.view_item', raise_exception=True)
def items(request: HttpRequest) -> HttpResponse:
    items = Item.objects.all()
    return render(request, 'warehouse/pages/items.html', {
        'title': 'Itens', 'items': items})


@login_required
@permission_required('warehouse.add_item', raise_exception=True)
def create_item(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('warehouse:items')

    form = ItemForm()
    return render(request, 'warehouse/pages/create_item.html', {
        'title': 'Criar Item', 'form': form})
