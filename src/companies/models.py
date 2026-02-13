from django.db import models
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


User = get_user_model()


class Company(models.Model):
    name = models.CharField(max_length=120)
    cnpj = models.CharField(max_length=14, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"
        permissions = [
            ("manage_company_features", "Can manage company feature activation"),
        ]

    def __str__(self) -> str:
        return self.name

    def has_feature(self, feature_code: str) -> bool:
        return self.feature_grants.filter(
            enabled=True,
            feature__is_active=True,
            feature__code=feature_code,
        ).exists()


class Employee(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="employee_profile"
    )
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, related_name="employees"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.company.name}"


class Feature(models.Model):
    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def clean(self):
        super().clean()
        valid_labels = {
            app_config.label for app_config in django_apps.get_app_configs()}
        if self.code not in valid_labels:
            raise ValidationError(
                {"code": "Feature code must match an installed app label."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.code


class CompanyFeature(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="feature_grants"
    )
    feature = models.ForeignKey(
        Feature, on_delete=models.CASCADE, related_name="company_grants"
    )
    enabled = models.BooleanField(default=True)
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_company_features",
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company__name", "feature__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "feature"],
                name="unique_company_feature_grant",
            )
        ]

    def __str__(self) -> str:
        state = "enabled" if self.enabled else "disabled"
        return f"{self.company.name} - {self.feature.code} ({state})"


def get_user_company(user: User) -> Company | None:
    if not getattr(user, "is_authenticated", False):
        return None

    employee = getattr(user, "employee_profile", None)
    if employee is None:
        return None
    return employee.company
