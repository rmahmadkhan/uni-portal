from __future__ import annotations

from datetime import date

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import (
    Announcement,
    Course,
    Enrollment,
    FeeInvoice,
    Grade,
    Section,
    SectionInstructor,
    Term,
    TranscriptRequest,
    TranscriptRequestEvent,
)
from portal.roles import (
    ROLE_ALUMNI,
    ROLE_FACULTY,
    ROLE_FINANCE,
    ROLE_IT_ADMIN,
    ROLE_REGISTRAR,
    ROLE_STUDENT,
    ensure_groups_exist,
)


class Command(BaseCommand):
    help = "Seed demo users and sample data for the University Portal."

    def handle(self, *args, **options):
        ensure_groups_exist()

        def mk_user(username: str, *, password: str, email: str, groups: list[str], is_staff: bool = False):
            user, created = User.objects.get_or_create(username=username)
            if created or not user.has_usable_password():
                user.set_password(password)
            user.email = email
            user.is_staff = user.is_staff or is_staff
            user.save()

            group_objs = Group.objects.filter(name__in=groups)
            user.groups.set(group_objs)
            return user

        student = mk_user("student1", password="password123", email="student1@example.edu", groups=[ROLE_STUDENT])
        faculty = mk_user("faculty1", password="password123", email="faculty1@example.edu", groups=[ROLE_FACULTY])
        registrar = mk_user("registrar1", password="password123", email="registrar1@example.edu", groups=[ROLE_REGISTRAR], is_staff=True)
        finance = mk_user("finance1", password="password123", email="finance1@example.edu", groups=[ROLE_FINANCE], is_staff=True)
        alumni = mk_user("alumni1", password="password123", email="alumni1@example.edu", groups=[ROLE_ALUMNI])
        itadmin = mk_user("admin1", password="password123", email="admin1@example.edu", groups=[ROLE_IT_ADMIN], is_staff=True)
        # Give the demo IT/Admin full Django-admin access to avoid permission confusion.
        itadmin.is_superuser = True
        itadmin.is_staff = True
        itadmin.save(update_fields=["is_superuser", "is_staff"])

        term, _ = Term.objects.get_or_create(
            name="Spring 2026",
            defaults={
                "start_date": date(2026, 1, 15),
                "end_date": date(2026, 5, 20),
                "is_active": True,
                "registration_start": timezone.now() - timezone.timedelta(days=7),
                "registration_end": timezone.now() + timezone.timedelta(days=7),
            },
        )
        Term.objects.exclude(id=term.id).update(is_active=False)

        cs101, _ = Course.objects.get_or_create(code="CS101", defaults={"title": "Intro to Computing", "credits": 3})
        cs201, _ = Course.objects.get_or_create(code="CS201", defaults={"title": "Data Structures", "credits": 3})

        s1, _ = Section.objects.get_or_create(term=term, course=cs101, section_code="A", defaults={"capacity": 40, "meeting_days": "Mon,Wed", "location": "LT-1"})
        s2, _ = Section.objects.get_or_create(term=term, course=cs201, section_code="A", defaults={"capacity": 35, "meeting_days": "Tue,Thu", "location": "LT-2"})

        SectionInstructor.objects.get_or_create(section=s1, instructor=faculty)
        SectionInstructor.objects.get_or_create(section=s2, instructor=faculty)

        Enrollment.objects.get_or_create(section=s1, student=student, defaults={"status": Enrollment.Status.ENROLLED})

        Grade.objects.update_or_create(section=s1, student=student, defaults={"value": "A", "released": True})

        FeeInvoice.objects.get_or_create(
            student=student,
            term=term,
            reference_no="INV-2026-0001",
            defaults={"amount": 125000.00, "due_date": date(2026, 2, 20), "status": FeeInvoice.Status.DUE},
        )

        Announcement.objects.get_or_create(
            title="Welcome to the Portal",
            defaults={
                "body": "This is seeded demo data. Login as student1/faculty1/etc with password123.",
                "created_by": itadmin,
                "is_pinned": True,
                "publish_at": timezone.now() - timezone.timedelta(days=1),
            },
        )

        tr, created = TranscriptRequest.objects.get_or_create(
            requester=student,
            purpose="Scholarship application",
            delivery_method=TranscriptRequest.DeliveryMethod.EMAIL,
            defaults={"recipient_details": "scholarships@example.org", "status": TranscriptRequest.Status.SUBMITTED},
        )
        if created:
            TranscriptRequestEvent.objects.create(request=tr, actor=student, from_status="", to_status=tr.status, note="Seeded request")

        self.stdout.write(self.style.SUCCESS("Seeded demo users and data."))
        self.stdout.write("Logins: student1, faculty1, registrar1, finance1, alumni1, admin1 (password: password123)")
