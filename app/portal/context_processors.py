from __future__ import annotations

from .roles import (
    ROLE_ALUMNI,
    ROLE_FACULTY,
    ROLE_FINANCE,
    ROLE_IT_ADMIN,
    ROLE_REGISTRAR,
    ROLE_STUDENT,
    user_in_any_group,
)


def portal_nav(request):
    user = request.user
    return {
        "nav": {
            "is_student": user_in_any_group(user, [ROLE_STUDENT]),
            "is_faculty": user_in_any_group(user, [ROLE_FACULTY]),
            "is_registrar": user_in_any_group(user, [ROLE_REGISTRAR, ROLE_IT_ADMIN]),
            "is_finance": user_in_any_group(user, [ROLE_FINANCE, ROLE_IT_ADMIN]),
            "is_alumni": user_in_any_group(user, [ROLE_ALUMNI]),
            "is_admin": user.is_authenticated and (user.is_superuser or user_in_any_group(user, [ROLE_IT_ADMIN])),
        }
    }
