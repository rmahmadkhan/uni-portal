from __future__ import annotations

from typing import Iterable

from django.contrib.auth.models import Group, User


ROLE_STUDENT = "Student"
ROLE_FACULTY = "Faculty"
ROLE_STAFF = "Staff"
ROLE_REGISTRAR = "Registrar Staff"
ROLE_FINANCE = "Finance Staff"
ROLE_IT_ADMIN = "IT/Admin"
ROLE_ALUMNI = "Alumni"

ALL_ROLES: list[str] = [
    ROLE_STUDENT,
    ROLE_FACULTY,
    ROLE_STAFF,
    ROLE_REGISTRAR,
    ROLE_FINANCE,
    ROLE_IT_ADMIN,
    ROLE_ALUMNI,
]


ROLE_KEY_GROUPS: dict[str, list[str]] = {
    "STUDENT": [ROLE_STUDENT],
    "FACULTY": [ROLE_FACULTY],
    "STAFF": [ROLE_STAFF],
    "REGISTRAR": [ROLE_REGISTRAR, ROLE_IT_ADMIN],
    "FINANCE": [ROLE_FINANCE, ROLE_IT_ADMIN],
    "ADMIN": [ROLE_IT_ADMIN],
    "IT_ADMIN": [ROLE_IT_ADMIN],
    "ALUMNI": [ROLE_ALUMNI],
}


def ensure_groups_exist() -> None:
    for role in ALL_ROLES:
        Group.objects.get_or_create(name=role)


def ensure_role_groups() -> None:
    ensure_groups_exist()


def user_in_any_group(user: User, group_names: Iterable[str]) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=list(group_names)).exists()


def is_in_role(user: User, role_key_or_group_name: str) -> bool:
    groups = ROLE_KEY_GROUPS.get(role_key_or_group_name)
    if groups is None:
        groups = [role_key_or_group_name]
    return user_in_any_group(user, groups)
