from __future__ import annotations

import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


class Term(models.Model):
	name = models.CharField(max_length=64, unique=True)
	start_date = models.DateField()
	end_date = models.DateField()
	is_active = models.BooleanField(default=False)

	registration_start = models.DateTimeField(null=True, blank=True)
	registration_end = models.DateTimeField(null=True, blank=True)

	def __str__(self) -> str:
		return self.name


class Course(models.Model):
	code = models.CharField(max_length=16, unique=True)
	title = models.CharField(max_length=200)
	department = models.CharField(max_length=50, blank=True)
	level = models.CharField(max_length=16, blank=True)
	credits = models.DecimalField(max_digits=4, decimal_places=1, default=3.0)
	description = models.TextField(blank=True)

	def __str__(self) -> str:
		return f"{self.code} — {self.title}"


class Section(models.Model):
	term = models.ForeignKey(Term, on_delete=models.PROTECT)
	course = models.ForeignKey(Course, on_delete=models.PROTECT)
	section_code = models.CharField(max_length=16, default="A")
	capacity = models.PositiveIntegerField(default=30)

	# Example: "Mon,Wed". Keep simple for MVP.
	meeting_days = models.CharField(max_length=32, blank=True)
	start_time = models.TimeField(null=True, blank=True)
	end_time = models.TimeField(null=True, blank=True)
	location = models.CharField(max_length=120, blank=True)

	def __str__(self) -> str:
		return f"{self.course.code}-{self.section_code} ({self.term.name})"

	@property
	def enrolled_count(self) -> int:
		return self.enrollments.filter(status=Enrollment.Status.ENROLLED).count()

	def has_seats(self) -> bool:
		return self.enrolled_count < self.capacity


class SectionInstructor(models.Model):
	section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="instructors")
	instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

	class Meta:
		unique_together = [("section", "instructor")]

	def __str__(self) -> str:
		return f"{self.instructor} -> {self.section}"


class Enrollment(models.Model):
	class Status(models.TextChoices):
		ENROLLED = "enrolled", "Enrolled"
		DROPPED = "dropped", "Dropped"
		WAITLISTED = "waitlisted", "Waitlisted"

	section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="enrollments")
	student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="enrollments")
	status = models.CharField(max_length=16, choices=Status.choices, default=Status.ENROLLED)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		unique_together = [("section", "student")]

	def __str__(self) -> str:
		return f"{self.student} — {self.section} ({self.status})"


class Grade(models.Model):
	section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="grades")
	student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	value = models.CharField(max_length=8, blank=True)
	released = models.BooleanField(default=False)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = [("section", "student")]

	def __str__(self) -> str:
		return f"{self.student} — {self.section}: {self.value}"


class Announcement(models.Model):
	title = models.CharField(max_length=200)
	body = models.TextField()
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	target_roles = models.ManyToManyField("auth.Group", blank=True)
	publish_at = models.DateTimeField(default=timezone.now)
	expire_at = models.DateTimeField(null=True, blank=True)
	is_pinned = models.BooleanField(default=False)
	created_at = models.DateTimeField(default=timezone.now)

	def __str__(self) -> str:
		return self.title

	def is_active(self, now=None) -> bool:
		now = now or timezone.now()
		if self.publish_at and self.publish_at > now:
			return False
		if self.expire_at and self.expire_at <= now:
			return False
		return True


class FeeInvoice(models.Model):
	class Status(models.TextChoices):
		DUE = "due", "Due"
		PAID = "paid", "Paid"
		OVERDUE = "overdue", "Overdue"

	student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	term = models.ForeignKey(Term, on_delete=models.PROTECT)
	reference_no = models.CharField(max_length=64, unique=True)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	due_date = models.DateField()
	status = models.CharField(max_length=16, choices=Status.choices, default=Status.DUE)

	def __str__(self) -> str:
		return f"{self.reference_no} ({self.student})"


class TranscriptRequest(models.Model):
	class Status(models.TextChoices):
		SUBMITTED = "submitted", "Submitted"
		IN_REVIEW = "in_review", "In Review"
		APPROVED = "approved", "Approved"
		REJECTED = "rejected", "Rejected"
		ISSUED = "issued", "Issued"

	class DeliveryMethod(models.TextChoices):
		EMAIL = "email", "Email"
		PICKUP = "pickup", "Pickup"
		COURIER = "courier", "Courier"

	requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	purpose = models.CharField(max_length=200)
	delivery_method = models.CharField(max_length=16, choices=DeliveryMethod.choices)
	recipient_details = models.TextField(blank=True)

	status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED)
	reviewed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="reviewed_transcripts"
	)
	review_reason = models.TextField(blank=True)
	issued_at = models.DateTimeField(null=True, blank=True)
	verification_code = models.CharField(max_length=24, blank=True)

	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f"TR-{self.id} ({self.requester})"

	def ensure_verification_code(self) -> str:
		if not self.verification_code:
			self.verification_code = secrets.token_urlsafe(12)[:16]
			self.save(update_fields=["verification_code"])
		return self.verification_code


class TranscriptRequestEvent(models.Model):
	request = models.ForeignKey(TranscriptRequest, on_delete=models.CASCADE, related_name="events")
	actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	from_status = models.CharField(max_length=16, blank=True)
	to_status = models.CharField(max_length=16)
	note = models.TextField(blank=True)
	created_at = models.DateTimeField(default=timezone.now)

	def __str__(self) -> str:
		return f"TR-{self.request_id}: {self.from_status}->{self.to_status}"


class SupportTicket(models.Model):
	class Status(models.TextChoices):
		OPEN = "open", "Open"
		IN_PROGRESS = "in_progress", "In Progress"
		RESOLVED = "resolved", "Resolved"
		CLOSED = "closed", "Closed"

	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="support_tickets")
	category = models.CharField(max_length=60)
	subject = models.CharField(max_length=200)
	description = models.TextField()
	status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
	assigned_to = models.ForeignKey(
		settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="assigned_tickets"
	)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f"TKT-{self.id}: {self.subject}"


class SupportMessage(models.Model):
	ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	message = models.TextField()
	created_at = models.DateTimeField(default=timezone.now)


class AuditLog(models.Model):
	actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
	action = models.CharField(max_length=80)
	entity_type = models.CharField(max_length=80)
	entity_id = models.CharField(max_length=64, blank=True)
	metadata = models.JSONField(default=dict, blank=True)
	ip = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.CharField(max_length=300, blank=True)
	created_at = models.DateTimeField(default=timezone.now)

	def __str__(self) -> str:
		return f"{self.created_at.isoformat()} {self.action} {self.entity_type}:{self.entity_id}"
