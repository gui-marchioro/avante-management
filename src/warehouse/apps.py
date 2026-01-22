from django.apps import AppConfig
from django.db.models.signals import post_migrate


class WarehouseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "warehouse"

    def ready(self):
        post_migrate.connect(create_warehouse_groups, sender=self)


def create_warehouse_groups(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    # Create warehouse_assistant group and assign permissions
    assistant_group, created = Group.objects.get_or_create(name="warehouse_assistant")
    if created:
        warehouse_models = ContentType.objects.filter(app_label="warehouse")
        # Exclude the special permission from the assistant group
        warehouse_permissions = Permission.objects.filter(
            content_type__in=warehouse_models
        ).exclude(codename="view_financial_dashboard")
        assistant_group.permissions.set(warehouse_permissions)

    # Create warehouse_admin group and assign all warehouse permissions
    admin_group, created = Group.objects.get_or_create(name="warehouse_admin")
    if created:
        warehouse_models = ContentType.objects.filter(app_label="warehouse")
        all_warehouse_permissions = Permission.objects.filter(
            content_type__in=warehouse_models
        )
        admin_group.permissions.set(all_warehouse_permissions)
