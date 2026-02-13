from django.contrib.auth.models import Group, Permission
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
def configure_standard_groups(sender, app_config, **kwargs):
    if app_config is None or app_config.label != "companies":
        return

    group_permissions_map: dict[str, list[tuple[str, str]]] = {
        "warehouse_viewer": [
            ("warehouse", "view_item"),
            ("warehouse", "view_itemtype"),
            ("warehouse", "view_manufacturer"),
            ("warehouse", "view_itemunit"),
        ],
        "warehouse_editor": [
            ("warehouse", "view_item"),
            ("warehouse", "view_itemtype"),
            ("warehouse", "view_manufacturer"),
            ("warehouse", "view_itemunit"),
            ("warehouse", "add_item"),
            ("warehouse", "add_itemtype"),
            ("warehouse", "add_manufacturer"),
            ("warehouse", "add_itemunit"),
            ("warehouse", "change_item"),
            ("warehouse", "change_itemtype"),
            ("warehouse", "change_manufacturer"),
            ("warehouse", "change_itemunit"),
        ],
        "warehouse_admin": [
            ("warehouse", "view_item"),
            ("warehouse", "view_itemtype"),
            ("warehouse", "view_manufacturer"),
            ("warehouse", "view_itemunit"),
            ("warehouse", "add_item"),
            ("warehouse", "add_itemtype"),
            ("warehouse", "add_manufacturer"),
            ("warehouse", "add_itemunit"),
            ("warehouse", "change_item"),
            ("warehouse", "change_itemtype"),
            ("warehouse", "change_manufacturer"),
            ("warehouse", "change_itemunit"),
            ("warehouse", "view_financial_dashboard"),
        ],
        "company_viewer": [
            ("companies", "view_company"),
            ("companies", "view_employee"),
        ],
        "company_editor": [
            ("companies", "view_company"),
            ("companies", "view_employee"),
            ("companies", "change_company"),
            ("companies", "change_employee"),
        ],
        "company_admin": [
            ("companies", "view_company"),
            ("companies", "view_employee"),
            ("companies", "change_company"),
            ("companies", "change_employee"),
            ("companies", "add_employee"),
            ("companies", "manage_company_features"),
            ("auth", "view_user"),
            ("auth", "change_user"),
            ("auth", "view_group"),
        ],
    }

    for group_name, required_permissions in group_permissions_map.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        permission_ids = []
        for app_label, codename in required_permissions:
            permission = Permission.objects.filter(
                content_type__app_label=app_label,
                codename=codename,
            ).first()
            if permission is not None:
                permission_ids.append(permission.id)
        group.permissions.set(permission_ids)
