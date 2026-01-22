from django.contrib.auth.models import User
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from .forms import RegisterForm


def register(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user: User = form.save()
            user.save()
            return redirect('users:login')
    else:
        form = RegisterForm()

    return render(request, 'users/pages/register.html', {'form': form})
