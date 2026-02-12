from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Company(models.Model):
    name = models.CharField(max_length=120)
    cnpj = models.CharField(max_length=14, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"

    def __str__(self) -> str:
        return self.name


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


def get_user_company(user: User) -> Company | None:
    if not getattr(user, "is_authenticated", False):
        return None

    employee = getattr(user, "employee_profile", None)
    if employee is None:
        return None
    return employee.company
