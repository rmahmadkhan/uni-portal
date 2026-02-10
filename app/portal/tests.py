from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Course, Enrollment, FeeInvoice, Section, SupportMessage, SupportTicket, Term, TranscriptRequest
from .roles import (
	ROLE_FINANCE,
	ROLE_IT_ADMIN,
	ROLE_REGISTRAR,
	ROLE_STUDENT,
	ensure_groups_exist,
)


class PortalSmokeTests(TestCase):
	def setUp(self):
		ensure_groups_exist()
		self.student = User.objects.create_user(username="student_test", password="password123")
		self.student.groups.add(Group.objects.get(name=ROLE_STUDENT))
		self.itadmin = User.objects.create_user(username="itadmin_test", password="password123")
		self.itadmin.groups.add(Group.objects.get(name=ROLE_IT_ADMIN))
		self.registrar = User.objects.create_user(username="registrar_test", password="password123")
		self.registrar.groups.add(Group.objects.get(name=ROLE_REGISTRAR))
		self.finance = User.objects.create_user(username="finance_test", password="password123")
		self.finance.groups.add(Group.objects.get(name=ROLE_FINANCE))

		self.term = Term.objects.create(
			name="Spring 2026",
			start_date=date.today() - timedelta(days=30),
			end_date=date.today() + timedelta(days=90),
			is_active=True,
			registration_start=timezone.now() - timedelta(days=1),
			registration_end=timezone.now() + timedelta(days=7),
		)
		self.course = Course.objects.create(code="CS101", title="Intro to CS")
		self.section = Section.objects.create(term=self.term, course=self.course, section_code="A", capacity=1)

	def test_healthz_is_ok(self):
		resp = self.client.get(reverse("portal:healthz"))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "ok")

	def test_login_page_renders(self):
		resp = self.client.get(reverse("portal:login"))
		self.assertEqual(resp.status_code, 200)

	def test_dashboard_requires_login(self):
		resp = self.client.get(reverse("portal:dashboard"))
		self.assertEqual(resp.status_code, 302)
		self.assertIn(reverse("portal:login"), resp["Location"])

	def test_student_can_login_and_view_dashboard(self):
		ok = self.client.login(username="student_test", password="password123")
		self.assertTrue(ok)
		resp = self.client.get(reverse("portal:dashboard"))
		self.assertEqual(resp.status_code, 200)

	def test_logout_via_post_logs_out(self):
		ok = self.client.login(username="student_test", password="password123")
		self.assertTrue(ok)
		resp = self.client.post(reverse("portal:logout"), follow=False)
		self.assertEqual(resp.status_code, 302)
		self.assertIn(reverse("portal:login"), resp["Location"])
		resp2 = self.client.get(reverse("portal:dashboard"), follow=False)
		self.assertEqual(resp2.status_code, 302)
		self.assertIn(reverse("portal:login"), resp2["Location"])

	def test_user_admin_page_requires_admin_role(self):
		ok = self.client.login(username="student_test", password="password123")
		self.assertTrue(ok)
		resp = self.client.get(reverse("portal:admin_users_new"))
		self.assertEqual(resp.status_code, 403)

	def test_it_admin_can_create_user_in_app(self):
		ok = self.client.login(username="itadmin_test", password="password123")
		self.assertTrue(ok)
		resp = self.client.post(
			reverse("portal:admin_users_new"),
			data={
				"username": "new_user_1",
				"email": "new_user_1@example.edu",
				"password1": "password123",
				"password2": "password123",
				"roles": [ROLE_STUDENT],
				"is_staff": "on",
			},
			follow=False,
		)
		self.assertEqual(resp.status_code, 302)
		self.assertIn(reverse("portal:admin_users_new"), resp["Location"])
		u = User.objects.get(username="new_user_1")
		self.assertTrue(u.is_staff)
		self.assertTrue(u.groups.filter(name=ROLE_STUDENT).exists())

	def test_courses_list_and_detail_render(self):
		ok = self.client.login(username="student_test", password="password123")
		self.assertTrue(ok)
		resp = self.client.get(reverse("portal:courses"))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "CS101")

		resp2 = self.client.get(reverse("portal:course_detail", kwargs={"code": "CS101"}))
		self.assertEqual(resp2.status_code, 200)
		self.assertContains(resp2, "Intro to CS")

	def test_course_detail_shows_enrolled_badge_when_enrolled(self):
		Enrollment.objects.create(section=self.section, student=self.student, status=Enrollment.Status.ENROLLED)
		ok = self.client.login(username="student_test", password="password123")
		self.assertTrue(ok)
		resp = self.client.get(reverse("portal:course_detail", kwargs={"code": "CS101"}))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "Enrolled")

	def test_registration_add_and_drop(self):
		ok = self.client.login(username="student_test", password="password123")
		self.assertTrue(ok)

		resp = self.client.post(
			reverse("portal:registration"),
			data={"action": "add", "section_id": str(self.section.id)},
			follow=False,
		)
		self.assertEqual(resp.status_code, 302)
		enr = Enrollment.objects.get(section=self.section, student=self.student)
		self.assertEqual(enr.status, Enrollment.Status.ENROLLED)

		resp2 = self.client.post(
			reverse("portal:registration"),
			data={"action": "drop", "section_id": str(self.section.id)},
			follow=False,
		)
		self.assertEqual(resp2.status_code, 302)
		enr.refresh_from_db()
		self.assertEqual(enr.status, Enrollment.Status.DROPPED)

	def test_transcript_request_create_student_and_process_registrar(self):
		ok = self.client.login(username="student_test", password="password123")
		self.assertTrue(ok)
		resp = self.client.post(
			reverse("portal:transcript_request_new"),
			data={
				"purpose": "Job application",
				"delivery_method": TranscriptRequest.DeliveryMethod.EMAIL,
				"recipient_details": "hr@example.com",
			},
			follow=False,
		)
		self.assertEqual(resp.status_code, 302)
		tr = TranscriptRequest.objects.get(requester=self.student)
		self.assertEqual(tr.status, TranscriptRequest.Status.SUBMITTED)

		# Student must not access registrar queue.
		resp2 = self.client.get(reverse("portal:registrar_queue"))
		self.assertEqual(resp2.status_code, 403)

		# Registrar can approve + issue.
		self.client.logout()
		ok2 = self.client.login(username="registrar_test", password="password123")
		self.assertTrue(ok2)
		resp3 = self.client.post(reverse("portal:registrar_approve", kwargs={"request_id": tr.id}), data={"reason": "OK"})
		self.assertEqual(resp3.status_code, 302)
		tr.refresh_from_db()
		self.assertEqual(tr.status, TranscriptRequest.Status.APPROVED)

		# Official PDF should not exist before issuance.
		resp4 = self.client.get(reverse("portal:official_transcript_pdf", kwargs={"request_id": tr.id}))
		self.assertEqual(resp4.status_code, 404)

		resp5 = self.client.post(reverse("portal:registrar_issue", kwargs={"request_id": tr.id}))
		self.assertEqual(resp5.status_code, 302)
		tr.refresh_from_db()
		self.assertEqual(tr.status, TranscriptRequest.Status.ISSUED)
		self.assertTrue(bool(tr.verification_code))
		self.assertIsNotNone(tr.issued_at)

		resp6 = self.client.get(reverse("portal:official_transcript_pdf", kwargs={"request_id": tr.id}))
		self.assertEqual(resp6.status_code, 200)
		self.assertIn("official_transcript_TR", resp6.get("Content-Disposition", ""))

	def test_unofficial_transcript_pdf_downloads_for_student(self):
		ok = self.client.login(username="student_test", password="password123")
		self.assertTrue(ok)
		resp = self.client.get(reverse("portal:unofficial_transcript_pdf"))
		self.assertEqual(resp.status_code, 200)
		self.assertIn("unofficial_transcript.pdf", resp.get("Content-Disposition", ""))

	def test_support_ticket_create_and_message(self):
		ok = self.client.login(username="student_test", password="password123")
		self.assertTrue(ok)
		resp = self.client.post(
			reverse("portal:support_new"),
			data={"category": "IT", "subject": "Login issue", "description": "Cannot login"},
			follow=False,
		)
		self.assertEqual(resp.status_code, 302)
		ticket = SupportTicket.objects.get(created_by=self.student)

		resp2 = self.client.post(
			reverse("portal:support_detail", kwargs={"ticket_id": ticket.id}),
			data={"message": "Additional details"},
			follow=False,
		)
		self.assertEqual(resp2.status_code, 302)
		self.assertTrue(SupportMessage.objects.filter(ticket=ticket, author=self.student).exists())

		# Another student should not see this ticket.
		other = User.objects.create_user(username="other_student", password="password123")
		other.groups.add(Group.objects.get(name=ROLE_STUDENT))
		self.client.logout()
		ok2 = self.client.login(username="other_student", password="password123")
		self.assertTrue(ok2)
		resp3 = self.client.get(reverse("portal:support_detail", kwargs={"ticket_id": ticket.id}))
		self.assertEqual(resp3.status_code, 404)

	def test_finance_student_and_finance_staff_views(self):
		FeeInvoice.objects.create(
			student=self.student,
			term=self.term,
			reference_no="INV-0001",
			amount="1234.50",
			due_date=date.today() + timedelta(days=10),
			status=FeeInvoice.Status.DUE,
		)

		ok = self.client.login(username="student_test", password="password123")
		self.assertTrue(ok)
		resp = self.client.get(reverse("portal:finance"))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "INV-0001")

		self.client.logout()
		ok2 = self.client.login(username="finance_test", password="password123")
		self.assertTrue(ok2)
		resp2 = self.client.get(reverse("portal:finance"))
		self.assertEqual(resp2.status_code, 200)
