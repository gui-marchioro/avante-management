from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [
    path(
        "users/login/",
        auth_views.LoginView.as_view(template_name="companies/pages/login.html"),
        name="login",
    ),
    path("users/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("users/register/", views.register_employee, name="register_employee"),
    path("signup/", views.signup_company, name="signup"),
]
