from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Company, Employee


User = get_user_model()


def validate_password_strength(value: str) -> None:
    if len(value) < 8:
        raise ValidationError(
            "Password must be at least 8 characters long.",
            code="invalid",
        )
    if not any(char.isdigit() for char in value):
        raise ValidationError(
            "Password must contain at least one numeral.",
            code="invalid",
        )
    if not any(char.isalpha() for char in value):
        raise ValidationError(
            "Password must contain at least one letter.",
            code="invalid",
        )
    if not any(char.isupper() for char in value):
        raise ValidationError(
            "Password must contain at least one uppercase letter.",
            code="invalid",
        )
    if not any(char.islower() for char in value):
        raise ValidationError(
            "Password must contain at least one lowercase letter.",
            code="invalid",
        )


class EmployeeRegisterForm(forms.ModelForm):  # type: ignore
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label="Senha",
        validators=[validate_password_strength],
    )
    password2 = forms.CharField(
        required=True, widget=forms.PasswordInput, label="Confirmar senha"
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password != password2:
            password_confirmation_error = ValidationError(
                "Passwords must be equal",
                code="invalid",
            )
            raise ValidationError(
                {
                    "password": password_confirmation_error,
                    "password2": password_confirmation_error,
                }
            )

        return cleaned_data

    @transaction.atomic
    def save(self, company: Company, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            Employee.objects.create(user=user, company=company)
        return user


class EmployeeUpdateForm(forms.ModelForm):  # type: ignore
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email"]

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        user_qs = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            user_qs = user_qs.exclude(pk=self.instance.pk)
        if user_qs.exists():
            raise ValidationError("This username is already in use.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        user_qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            user_qs = user_qs.exclude(pk=self.instance.pk)
        if user_qs.exists():
            raise ValidationError("This email is already in use.")
        return email


class EmployeeGroupsForm(forms.Form):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Groups",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].queryset = Group.objects.order_by("name")


class CompanyUpdateForm(forms.ModelForm):  # type: ignore
    cnpj = forms.CharField(max_length=18, required=False, label="CNPJ")

    class Meta:
        model = Company
        fields = ["name", "cnpj"]

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_cnpj(self):
        raw_cnpj = (self.cleaned_data.get("cnpj") or "").strip()
        if raw_cnpj == "":
            return None

        cnpj = "".join(char for char in raw_cnpj if char.isdigit())
        if len(cnpj) != 14:
            raise ValidationError("CNPJ must contain 14 digits.")

        company_qs = Company.objects.filter(cnpj=cnpj)
        if self.instance.pk:
            company_qs = company_qs.exclude(pk=self.instance.pk)
        if company_qs.exists():
            raise ValidationError("A company with this CNPJ already exists.")
        return cnpj


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
        cnpj = "".join(
            char for char in self.cleaned_data["cnpj"] if char.isdigit())
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
        company_admin_group = Group.objects.filter(
            name="company_admin").first()
        if company_admin_group is not None:
            user.groups.add(company_admin_group)
        Employee.objects.create(user=user, company=company)
        return user
