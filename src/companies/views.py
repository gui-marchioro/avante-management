from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.urls import NoReverseMatch, reverse
from .feature_routes import FEATURE_ROUTE_NAMES
from django.shortcuts import render, redirect
from .forms import CompanySignupForm, CompanyUpdateForm, EmployeeRegisterForm
from .models import CompanyFeature, Feature, get_user_company, Employee


@login_required
def home(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    if company is None:
        raise PermissionDenied("User is not associated with a company.")

    grants = {
        grant.feature_id: grant
        for grant in CompanyFeature.objects.filter(company=company).select_related("feature")
    }
    features = Feature.objects.filter(is_active=True).order_by("code")

    feature_cards = []
    for feature in features:
        grant = grants.get(feature.id)
        is_granted = grant is not None
        is_enabled = bool(is_granted and grant.enabled)

        route_name = FEATURE_ROUTE_NAMES.get(feature.code)
        target_url = None
        if route_name and is_enabled:
            try:
                target_url = reverse(route_name)
            except NoReverseMatch:
                target_url = None

        feature_cards.append(
            {
                "code": feature.code,
                "name": feature.name,
                "description": feature.description,
                "is_granted": is_granted,
                "is_enabled": is_enabled,
                "target_url": target_url,
            }
        )

    return render(
        request,
        "companies/pages/home.html",
        {
            "title": "Início",
            "company": company,
            "feature_cards": feature_cards,
            "employees": company.employees.select_related("user").all(),
        },
    )


def signup_company(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("companies:home")

    if request.method == "POST":
        form = CompanySignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("companies:home")
    else:
        form = CompanySignupForm()

    return render(
        request,
        "companies/pages/signup_company.html",
        {"title": "Criar Empresa", "form": form},
    )

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


@login_required
@permission_required("companies.add_employee", raise_exception=True)
@permission_required("companies.manage_company_features", raise_exception=True)
def company_configuration(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    if company is None:
        raise PermissionDenied("User is not associated with a company.")

    grants = list(
        CompanyFeature.objects.filter(company=company)
        .select_related("feature")
        .order_by("feature__code")
    )
    employees = company.employees.select_related("user").order_by("user__username")

    company_form = CompanyUpdateForm(instance=company)
    employee_form = EmployeeRegisterForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_company":
            company_form = CompanyUpdateForm(request.POST, instance=company)
            if company_form.is_valid():
                company_form.save()
                return redirect("companies:company_configuration")

        elif action == "toggle_features":
            for grant in grants:
                grant.enabled = f"feature_{grant.id}" in request.POST
            CompanyFeature.objects.bulk_update(grants, ["enabled", "updated_at"])
            return redirect("companies:company_configuration")

        elif action == "add_employee":
            employee_form = EmployeeRegisterForm(request.POST)
            if employee_form.is_valid():
                employee_form.save(company=company)
                return redirect("companies:company_configuration")

        elif action == "remove_employee":
            employee_id = request.POST.get("employee_id")
            if employee_id:
                employee = company.employees.filter(pk=employee_id).first()
                if employee and employee.user_id != request.user.id:
                    employee.user.delete()
            return redirect("companies:company_configuration")

    return render(
        request,
        "companies/pages/company_configuration.html",
        {
            "title": "Configurações da Empresa",
            "company": company,
            "company_form": company_form,
            "employee_form": employee_form,
            "employees": employees,
            "grants": grants,
        },
    )
