from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpRequest
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .forms import ItemForm
from .models import Item
from companies.models import get_user_company


@login_required
def home(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    if company is None:
        raise PermissionDenied("User is not associated with a company.")
    items = Item.objects.filter(company=company)
    if request.user.has_perm('warehouse.view_financial_dashboard'):
        return render(request, 'warehouse/pages/home.html',
                      {'title': 'Estoque', 'items': items})
    else:
        return redirect('warehouse:items')


@login_required
def items(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    if company is None:
        raise PermissionDenied("User is not associated with a company.")

    if not request.user.has_perm("warehouse.view_item"):
        raise PermissionDenied("You do not have permission to view items.")

    can_add_item = request.user.has_perm("warehouse.add_item")
    can_change_item = request.user.has_perm("warehouse.change_item")
    can_delete_item = request.user.has_perm("warehouse.delete_item")

    bound_update_form_item_id: int | None = None
    bound_update_form: ItemForm | None = None

    if request.method == "POST":
        action = request.POST.get("action")
        item_id = request.POST.get("item_id")

        if action in {"update_item", "delete_item"}:
            item = Item.objects.filter(company=company, pk=item_id).first()
            if item is None:
                return redirect("warehouse:items")

            if action == "update_item":
                if not can_change_item:
                    raise PermissionDenied("You do not have permission to change items.")
                bound_update_form_item_id = item.id
                bound_update_form = ItemForm(
                    request.POST,
                    instance=item,
                    company=company,
                    prefix=f"edit-{item.id}",
                )
                if bound_update_form.is_valid():
                    bound_update_form.save()
                    return redirect("warehouse:items")

            elif action == "delete_item":
                if not can_delete_item:
                    raise PermissionDenied("You do not have permission to delete items.")
                item.delete()
                return redirect("warehouse:items")

    items = list(
        Item.objects.filter(company=company).select_related("type", "manufacturer")
    )
    item_rows = []
    for item in items:
        edit_form = None
        if can_change_item:
            if bound_update_form_item_id == item.id and bound_update_form is not None:
                edit_form = bound_update_form
            else:
                edit_form = ItemForm(instance=item, company=company, prefix=f"edit-{item.id}")
        item_rows.append({"item": item, "edit_form": edit_form})

    return render(
        request,
        "warehouse/pages/items.html",
        {
            "title": "Itens",
            "items": items,
            "item_rows": item_rows,
            "can_add_item": can_add_item,
            "can_change_item": can_change_item,
            "can_delete_item": can_delete_item,
        },
    )


@login_required
def create_item(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    if company is None:
        raise PermissionDenied("User is not associated with a company.")
    if not request.user.has_perm("warehouse.add_item"):
        raise PermissionDenied("You do not have permission to add items.")

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
