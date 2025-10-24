# type: ignore
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test


def is_in_group(user: User, group_name: str | list[str]) -> bool:
    if isinstance(group_name, list):
        return user.is_authenticated and any(user.groups.filter(name=grp).exists() for grp in group_name)
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def group_required(group_name: str | list[str]):
    def in_group(user: User) -> bool:
        if isinstance(group_name, list):
            return user.is_authenticated and any(user.groups.filter(name=grp).exists() for grp in group_name)
        return user.is_authenticated and user.groups.filter(name=group_name).exists()
    return user_passes_test(in_group)
