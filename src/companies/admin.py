from django.contrib import admin
from .models import Company, CompanyFeature, Employee, Feature


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


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(CompanyFeature)
class CompanyFeatureAdmin(admin.ModelAdmin):
    list_display = ("company", "feature", "enabled", "granted_by", "granted_at")
    list_filter = ("enabled", "feature", "company")
    search_fields = ("company__name", "feature__code", "feature__name")

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if obj.granted_by_id is None:
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)
