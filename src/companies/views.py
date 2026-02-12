from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from .forms import CompanySignupForm, EmployeeRegisterForm
from .models import CompanyFeature, get_user_company


def signup_company(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("warehouse:home")

    if request.method == "POST":
        form = CompanySignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("warehouse:home")
    else:
        form = CompanySignupForm()

    return render(
        request,
        "companies/pages/signup_company.html",
        {"title": "Criar Empresa", "form": form},
    )


@login_required
@permission_required("companies.add_employee", raise_exception=True)
def register_employee(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    if company is None:
        raise PermissionDenied("User is not associated with a company.")

    if request.method == "POST":
        form = EmployeeRegisterForm(request.POST)
        if form.is_valid():
            form.save(company=company)
            return redirect("companies:register_employee")
    else:
        form = EmployeeRegisterForm()

    return render(request, "companies/pages/register_employee.html", {"form": form})


@login_required
@permission_required("companies.manage_company_features", raise_exception=True)
def company_features(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    if company is None:
        raise PermissionDenied("User is not associated with a company.")

    grants = list(
        CompanyFeature.objects.filter(company=company)
        .select_related("feature")
        .order_by("feature__code")
    )

    if request.method == "POST":
        for grant in grants:
            grant.enabled = f"feature_{grant.id}" in request.POST
        CompanyFeature.objects.bulk_update(grants, ["enabled", "updated_at"])
        return redirect("companies:company_features")

    return render(
        request,
        "companies/pages/company_features.html",
        {"grants": grants, "company": company},
    )
