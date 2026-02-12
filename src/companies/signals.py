from django.contrib.auth.models import Permission
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from .models import Company, CompanyFeature, Feature


@receiver(post_save, sender=Company)
def ensure_companies_feature_enabled(sender, instance: Company, created: bool, **kwargs):
    if not created:
        return

    feature, _ = Feature.objects.get_or_create(
        code="companies",
        defaults={"name": "Companies", "is_active": True},
    )
    CompanyFeature.objects.get_or_create(
        company=instance,
        feature=feature,
        defaults={"enabled": True},
    )


@receiver(post_migrate)
def grant_feature_management_to_company_admins(sender, app_config, **kwargs):
    if app_config is None or app_config.label != "companies":
        return

    add_employee_permission = Permission.objects.filter(
        content_type__app_label="companies",
        codename="add_employee",
    ).first()
    manage_features_permission = Permission.objects.filter(
        content_type__app_label="companies",
        codename="manage_company_features",
    ).first()

    if add_employee_permission is None or manage_features_permission is None:
        return

    for user in add_employee_permission.user_set.all():
        user.user_permissions.add(manage_features_permission)
