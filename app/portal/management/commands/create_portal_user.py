from __future__ import annotations

import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from ...roles import ALL_ROLES, ROLE_KEY_GROUPS, ensure_groups_exist


class Command(BaseCommand):
    help = "Create a portal user and optionally assign role groups."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--email", default="")
        parser.add_argument(
            "--password",
            default=None,
            help="Password for the user. If omitted, you will be prompted.",
        )
        parser.add_argument(
            "--roles",
            default="",
            help=(
                "Comma-separated role keys or group names (e.g. STUDENT,FACULTY or 'Student,Faculty'). "
                "Role keys: " + ",".join(sorted(ROLE_KEY_GROUPS.keys()))
            ),
        )
        parser.add_argument("--staff", action="store_true", help="Set is_staff=True")
        parser.add_argument("--superuser", action="store_true", help="Create as superuser")

    def handle(self, *args, **options):
        ensure_groups_exist()

        username: str = options["username"]
        email: str = options["email"]
        password: str | None = options["password"]
        roles_raw: str = options["roles"]
        is_staff: bool = options["staff"]
        is_superuser: bool = options["superuser"]

        if not password:
            password = getpass.getpass("Password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                raise CommandError("Passwords do not match.")

        roles: list[str] = [r.strip() for r in roles_raw.split(",") if r.strip()]

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise CommandError(f"User '{username}' already exists.")

        if is_superuser:
            user = User.objects.create_superuser(username=username, email=email, password=password)
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            if is_staff:
                user.is_staff = True
                user.save(update_fields=["is_staff"])

        added_groups: list[str] = []
        if roles:
            group_names: list[str] = []
            for role in roles:
                group_names.extend(ROLE_KEY_GROUPS.get(role, [role]))

            # Validate groups (catch typos early)
            valid_group_names = set(ALL_ROLES)
            unknown = [g for g in set(group_names) if g not in valid_group_names]
            if unknown:
                raise CommandError(
                    "Unknown group(s): "
                    + ", ".join(sorted(unknown))
                    + ". Valid groups: "
                    + ", ".join(ALL_ROLES)
                )

            for group_name in sorted(set(group_names)):
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
                added_groups.append(group_name)

        self.stdout.write(self.style.SUCCESS(f"Created user: {username}"))
        if email:
            self.stdout.write(f"Email: {email}")
        if is_superuser:
            self.stdout.write("Flags: superuser")
        elif is_staff:
            self.stdout.write("Flags: staff")
        if added_groups:
            self.stdout.write("Groups: " + ", ".join(added_groups))
        else:
            self.stdout.write("Groups: (none)")
