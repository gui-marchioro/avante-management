from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.urls import NoReverseMatch, reverse
from .feature_routes import FEATURE_ROUTE_NAMES
from django.shortcuts import render, redirect
from .forms import (
    CompanySignupForm,
    CompanyUpdateForm,
    EmployeeGroupsForm,
    EmployeeRegisterForm,
    EmployeeUpdateForm,
)
from .models import CompanyFeature, Feature, get_user_company


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


@login_required
def employees(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    if company is None:
        raise PermissionDenied("User is not associated with a company.")

    can_add_employee = request.user.has_perm("companies.add_employee")
    can_change_employee = request.user.has_perm("companies.change_employee")
    can_delete_employee = request.user.has_perm("companies.delete_employee")
    can_change_employee_groups = request.user.has_perm(
        "auth.change_user"
    ) and request.user.has_perm("auth.view_group")

    add_form = EmployeeRegisterForm(prefix="add") if can_add_employee else None

    bound_update_form_employee_id: int | None = None
    bound_group_form_employee_id: int | None = None
    bound_update_form: EmployeeUpdateForm | None = None
    bound_group_form: EmployeeGroupsForm | None = None

    if request.method == "POST":
        action = request.POST.get("action")
        employee_id = request.POST.get("employee_id")

        if action == "add_employee":
            if not can_add_employee:
                raise PermissionDenied("You do not have permission to add employees.")
            add_form = EmployeeRegisterForm(request.POST, prefix="add")
            if add_form.is_valid():
                add_form.save(company=company)
                return redirect("companies:employees")

        if action in {"update_employee", "delete_employee", "update_employee_groups"}:
            employee = (
                company.employees.select_related("user")
                .filter(pk=employee_id)
                .first()
            )
            if employee is None:
                return redirect("companies:employees")

            if action == "update_employee":
                if not can_change_employee:
                    raise PermissionDenied(
                        "You do not have permission to change employees."
                    )
                bound_update_form_employee_id = employee.id
                bound_update_form = EmployeeUpdateForm(
                    request.POST,
                    instance=employee.user,
                    prefix=f"edit-{employee.id}",
                )
                if bound_update_form.is_valid():
                    bound_update_form.save()
                    return redirect("companies:employees")

            elif action == "delete_employee":
                if not can_delete_employee:
                    raise PermissionDenied(
                        "You do not have permission to delete employees."
                    )
                if employee.user_id != request.user.id:
                    employee.user.delete()
                return redirect("companies:employees")

            elif action == "update_employee_groups":
                if not can_change_employee_groups:
                    raise PermissionDenied(
                        "You do not have permission to change employee groups."
                    )
                bound_group_form_employee_id = employee.id
                bound_group_form = EmployeeGroupsForm(
                    request.POST,
                    prefix=f"groups-{employee.id}",
                )
                if bound_group_form.is_valid():
                    employee.user.groups.set(bound_group_form.cleaned_data["groups"])
                    return redirect("companies:employees")

    employees = list(
        company.employees.select_related("user").order_by("user__username")
    )
    employee_rows = []
    for employee in employees:
        edit_form = None
        if can_change_employee:
            if (
                bound_update_form_employee_id == employee.id
                and bound_update_form is not None
            ):
                edit_form = bound_update_form
            else:
                edit_form = EmployeeUpdateForm(
                    instance=employee.user,
                    prefix=f"edit-{employee.id}",
                )

        groups_form = None
        if can_change_employee_groups:
            if (
                bound_group_form_employee_id == employee.id
                and bound_group_form is not None
            ):
                groups_form = bound_group_form
            else:
                groups_form = EmployeeGroupsForm(
                    prefix=f"groups-{employee.id}",
                    initial={"groups": employee.user.groups.all()},
                )
        employee_rows.append(
            {"employee": employee, "edit_form": edit_form, "groups_form": groups_form}
        )

    return render(
        request,
        "companies/pages/employees.html",
        {
            "title": "Funcionários",
            "company": company,
            "employees": employees,
            "can_add_employee": can_add_employee,
            "can_change_employee": can_change_employee,
            "can_delete_employee": can_delete_employee,
            "can_change_employee_groups": can_change_employee_groups,
            "add_form": add_form,
            "employee_rows": employee_rows,
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
def company_configuration(request: HttpRequest) -> HttpResponse:
    company = get_user_company(request.user)
    if company is None:
        raise PermissionDenied("User is not associated with a company.")

    can_change_company = request.user.has_perm("companies.change_company")
    can_manage_company_features = request.user.has_perm(
        "companies.manage_company_features"
    )
    can_add_employee = request.user.has_perm("companies.add_employee")
    can_change_employee = request.user.has_perm("companies.change_employee")
    can_delete_employee = request.user.has_perm("companies.delete_employee")
    can_change_employee_groups = request.user.has_perm(
        "auth.change_user"
    ) and request.user.has_perm("auth.view_group")

    grants = []
    if can_manage_company_features:
        grants = list(
            CompanyFeature.objects.filter(company=company)
            .select_related("feature")
            .order_by("feature__code")
        )

    company_form = CompanyUpdateForm(instance=company) if can_change_company else None
    employee_form = EmployeeRegisterForm(
        prefix="add") if can_add_employee else None
    bound_update_form_employee_id: int | None = None
    bound_group_form_employee_id: int | None = None
    bound_update_form: EmployeeUpdateForm | None = None
    bound_group_form: EmployeeGroupsForm | None = None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_company":
            if not can_change_company:
                raise PermissionDenied("You do not have permission to update company data.")
            company_form = CompanyUpdateForm(request.POST, instance=company)
            if company_form.is_valid():
                company_form.save()
                return redirect("companies:company_configuration")

        elif action == "toggle_features":
            if not can_manage_company_features:
                raise PermissionDenied("You do not have permission to manage features.")
            for grant in grants:
                grant.enabled = f"feature_{grant.id}" in request.POST
            CompanyFeature.objects.bulk_update(
                grants, ["enabled", "updated_at"])
            return redirect("companies:company_configuration")

        elif action == "add_employee":
            if not can_add_employee:
                raise PermissionDenied("You do not have permission to add employees.")
            employee_form = EmployeeRegisterForm(request.POST, prefix="add")
            if employee_form.is_valid():
                employee_form.save(company=company)
                return redirect("companies:company_configuration")

        elif action == "remove_employee":
            if not can_delete_employee:
                raise PermissionDenied("You do not have permission to remove employees.")
            employee_id = request.POST.get("employee_id")
            if employee_id:
                employee = company.employees.filter(pk=employee_id).first()
                if employee and employee.user_id != request.user.id:
                    employee.user.delete()
            return redirect("companies:company_configuration")

        elif action == "update_employee":
            if not can_change_employee:
                raise PermissionDenied("You do not have permission to change employees.")
            employee_id = request.POST.get("employee_id")
            employee = company.employees.select_related("user").filter(pk=employee_id).first()
            if employee is None:
                return redirect("companies:company_configuration")
            bound_update_form_employee_id = employee.id
            bound_update_form = EmployeeUpdateForm(
                request.POST,
                instance=employee.user,
                prefix=f"edit-{employee.id}",
            )
            if bound_update_form.is_valid():
                bound_update_form.save()
                return redirect("companies:company_configuration")

        elif action == "update_employee_groups":
            if not can_change_employee_groups:
                raise PermissionDenied(
                    "You do not have permission to change employee groups."
                )
            employee_id = request.POST.get("employee_id")
            employee = company.employees.select_related("user").filter(pk=employee_id).first()
            if employee is None:
                return redirect("companies:company_configuration")
            bound_group_form_employee_id = employee.id
            bound_group_form = EmployeeGroupsForm(
                request.POST,
                prefix=f"groups-{employee.id}",
            )
            if bound_group_form.is_valid():
                employee.user.groups.set(bound_group_form.cleaned_data["groups"])
                return redirect("companies:company_configuration")

    employees = list(
        company.employees.select_related("user").order_by("user__username")
    )
    employee_rows = []
    for employee in employees:
        edit_form = None
        groups_form = None
        if can_change_employee:
            if (
                bound_update_form_employee_id == employee.id
                and bound_update_form is not None
            ):
                edit_form = bound_update_form
            else:
                edit_form = EmployeeUpdateForm(
                    instance=employee.user,
                    prefix=f"edit-{employee.id}",
                )
        if can_change_employee_groups:
            if (
                bound_group_form_employee_id == employee.id
                and bound_group_form is not None
            ):
                groups_form = bound_group_form
            else:
                groups_form = EmployeeGroupsForm(
                    prefix=f"groups-{employee.id}",
                    initial={"groups": employee.user.groups.all()},
                )
        employee_rows.append(
            {"employee": employee, "edit_form": edit_form, "groups_form": groups_form}
        )

    return render(
        request,
        "companies/pages/company_configuration.html",
        {
            "title": "Configurações da Empresa",
            "company": company,
            "company_form": company_form,
            "employee_form": employee_form,
            "employees": employees,
            "employee_rows": employee_rows,
            "grants": grants,
            "can_change_company": can_change_company,
            "can_manage_company_features": can_manage_company_features,
            "can_add_employee": can_add_employee,
            "can_change_employee": can_change_employee,
            "can_delete_employee": can_delete_employee,
            "can_change_employee_groups": can_change_employee_groups,
        },
    )
