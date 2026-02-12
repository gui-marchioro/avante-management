from django.contrib import admin
from .models import Company, Employee


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "created_at")
    list_filter = ("company",)
    search_fields = ("user__username", "user__email", "company__name")
