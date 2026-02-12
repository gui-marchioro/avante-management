from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpRequest
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .forms import ItemForm
from .models import Item
from companies.models import get_user_company


@login_required
def home(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    items = Item.objects.filter(company=company)
    if request.user.has_perm('warehouse.view_financial_dashboard'):
        return render(request, 'warehouse/pages/home.html',
                      {'title': 'Estoque', 'items': items})
    else:
        return redirect('warehouse:items')


@login_required
@permission_required('warehouse.view_item', raise_exception=True)
def items(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    items = Item.objects.filter(company=company)
    return render(request, 'warehouse/pages/items.html', {
        'title': 'Itens', 'items': items})


@login_required
@permission_required('warehouse.add_item', raise_exception=True)
def create_item(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    if company is None:
        raise PermissionDenied("User is not associated with a company.")

    if request.method == 'POST':
        form = ItemForm(request.POST, company=company)
        if form.is_valid():
            item = form.save(commit=False)
            item.company = company
            item.save()
            return redirect('warehouse:items')

    form = ItemForm(company=company)
    return render(request, 'warehouse/pages/create_item.html', {
        'title': 'Criar Item', 'form': form})
