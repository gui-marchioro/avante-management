from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import transaction
from users.forms import validate_password_strength
from users.models import Employee
from .models import Company


User = get_user_model()


class CompanySignupForm(forms.Form):
    company_name = forms.CharField(max_length=120, label="Empresa")
    cnpj = forms.CharField(max_length=18, label="CNPJ")
    first_name = forms.CharField(max_length=150, label="Nome")
    last_name = forms.CharField(max_length=150, label="Sobrenome")
    username = forms.CharField(max_length=150, label="Usuário")
    email = forms.EmailField(label="Email")
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label="Senha",
        validators=[validate_password_strength],
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label="Confirmar senha",
    )

    def clean_company_name(self):
        return self.cleaned_data["company_name"].strip()

    def clean_cnpj(self):
        cnpj = "".join(char for char in self.cleaned_data["cnpj"] if char.isdigit())
        if len(cnpj) != 14:
            raise ValidationError("CNPJ must contain 14 digits.")
        if Company.objects.filter(cnpj=cnpj).exists():
            raise ValidationError("A company with this CNPJ already exists.")
        return cnpj

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already in use.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password != password2:
            raise ValidationError("Passwords must be equal")
        return cleaned_data

    @transaction.atomic
    def save(self) -> User:
        company = Company.objects.create(
            name=self.cleaned_data["company_name"].strip(),
            cnpj=self.cleaned_data["cnpj"],
        )
        user = User.objects.create_user(
            first_name=self.cleaned_data["first_name"].strip(),
            last_name=self.cleaned_data["last_name"].strip(),
            username=self.cleaned_data["username"].strip(),
            email=self.cleaned_data["email"].strip().lower(),
            password=self.cleaned_data["password"],
        )
        warehouse_permissions = Permission.objects.filter(
            content_type__app_label="warehouse"
        )
        user.user_permissions.add(*warehouse_permissions)
        Employee.objects.create(user=user, company=company)
        return user
