from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from .forms import CompanySignupForm


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
