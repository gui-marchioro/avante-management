from django.contrib.auth.models import Group, User
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from .forms import RegisterForm
from . import groups


def register(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user: User = form.save()
            group = Group.objects.get(name=groups.DEFAULT)
            user.groups.add(group)
            user.save()
            return redirect('users:login')
    else:
        form = RegisterForm()

    return render(request, 'users/pages/register.html', {'form': form})
