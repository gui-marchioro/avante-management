from django.apps import AppConfig
from django.db.models.signals import post_migrate
from . import groups


def create_default_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    for name in [groups.DEFAULT, groups.MANAGER]:
        Group.objects.get_or_create(name=name)


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Auto create user groups
        # Import here to avoid crash due to app registry not ready
        post_migrate.connect(create_default_groups, sender=self)
