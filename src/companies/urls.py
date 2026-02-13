from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [
    path("", views.home, name="home"),
    path("employees/", views.employees, name="employees"),
    path(
        "users/login/",
        auth_views.LoginView.as_view(template_name="companies/pages/login.html"),
        name="login",
    ),
    path("users/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("companies/features/", views.company_features, name="company_features"),
    path("companies/config/", views.company_configuration, name="company_configuration"),
    path("signup/", views.signup_company, name="signup"),
]
