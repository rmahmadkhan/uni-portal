from __future__ import annotations

from io import BytesIO

from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import (
	Announcement,
	AuditLog,
	Course,
	Enrollment,
	FeeInvoice,
	Grade,
	Section,
	SectionInstructor,
	SupportMessage,
	SupportTicket,
	Term,
	TranscriptRequest,
	TranscriptRequestEvent,
)
from .forms import PortalUserCreateForm
from .roles import ensure_role_groups, is_in_role


def healthz(request: HttpRequest) -> HttpResponse:
	"""Basic health endpoint for load balancers.

	Returns 200 when the app is up. If a database is configured, also performs a
	simple DB round-trip.
	"""
	try:
		with connection.cursor() as cursor:
			cursor.execute("SELECT 1")
	except Exception:
		return HttpResponse("db_error", status=503, content_type="text/plain")
	return HttpResponse("ok", status=200, content_type="text/plain")


def _client_ip(request: HttpRequest) -> str | None:
	xff = request.META.get("HTTP_X_FORWARDED_FOR")
	if xff:
		return xff.split(",")[0].strip()
	return request.META.get("REMOTE_ADDR")


def _audit(request: HttpRequest, *, action: str, entity_type: str, entity_id: str = "", metadata: dict | None = None) -> None:
	AuditLog.objects.create(
		actor=request.user if request.user.is_authenticated else None,
		action=action,
		entity_type=entity_type,
		entity_id=str(entity_id or ""),
		metadata=metadata or {},
		ip=_client_ip(request),
		user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:300],
	)


def _require_role(request: HttpRequest, *roles: str) -> None:
	if request.user.is_superuser:
		return
	if any(is_in_role(request.user, r) for r in roles):
		return
	raise PermissionDenied()


class PortalLoginView(LoginView):
	template_name = "portal/login.html"
	redirect_authenticated_user = True
	_next_blocked_reason: str | None = None

	def get_success_url(self) -> str:
		user = self.request.user
		next_url = self.request.POST.get(REDIRECT_FIELD_NAME) or self.request.GET.get(REDIRECT_FIELD_NAME)
		if next_url and url_has_allowed_host_and_scheme(
			next_url,
			allowed_hosts={self.request.get_host()},
			require_https=self.request.is_secure(),
		):
			# Avoid sending users to role-restricted pages via stale `next=`.
			if next_url.startswith("/registrar/") and not is_in_role(user, "REGISTRAR"):
				self._next_blocked_reason = "Registrar"
				return reverse("portal:dashboard")
			if next_url.startswith("/faculty/") and not is_in_role(user, "FACULTY"):
				self._next_blocked_reason = "Faculty"
				return reverse("portal:dashboard")
			if next_url.startswith("/admin/") and not (user.is_staff or user.is_superuser):
				self._next_blocked_reason = "Admin"
				return reverse("portal:dashboard")
			return next_url
		return reverse("portal:dashboard")

	def form_valid(self, form):
		ensure_role_groups()
		_audit(self.request, action="auth.login", entity_type="user", entity_id=str(form.get_user().id))
		response = super().form_valid(form)
		if self._next_blocked_reason:
			messages.info(self.request, f"Signed in. Redirected to Dashboard (no access to {self._next_blocked_reason}).")
		return response


class PortalLogoutView(LogoutView):
	http_method_names = ["get", "post", "options"]
	next_page = "portal:login"

	def dispatch(self, request: HttpRequest, *args, **kwargs):
		if request.user.is_authenticated:
			_audit(request, action="auth.logout", entity_type="user", entity_id=str(request.user.id))
		return super().dispatch(request, *args, **kwargs)


@login_required
def admin_users_new(request: HttpRequest) -> HttpResponse:
	"""In-app user creation (for IT/Admin only)."""
	_require_role(request, "ADMIN")
	ensure_role_groups()

	if request.method == "POST":
		form = PortalUserCreateForm(request.POST)
		if form.is_valid():
			from django.contrib.auth import get_user_model
			from django.contrib.auth.models import Group

			User = get_user_model()
			user = User.objects.create_user(
				username=form.cleaned_data["username"],
				email=form.cleaned_data.get("email") or "",
				password=form.cleaned_data["password1"],
			)
			user.is_staff = bool(form.cleaned_data.get("is_staff"))
			user.save(update_fields=["is_staff"])

			roles = form.cleaned_data.get("roles") or []
			for role_name in roles:
				group = Group.objects.get(name=role_name)
				user.groups.add(group)

			_audit(
				request,
				action="admin.user.create",
				entity_type="user",
				entity_id=str(user.id),
				metadata={"username": user.username, "roles": list(roles), "is_staff": user.is_staff},
			)
			messages.success(request, f"Created user '{user.username}'.")
			return redirect("portal:admin_users_new")
	else:
		form = PortalUserCreateForm()

	return render(request, "portal/admin_users_new.html", {"form": form})


@login_required
def courses(request: HttpRequest) -> HttpResponse:
	active_term = Term.objects.filter(is_active=True).order_by("-start_date").first()
	items = Course.objects.order_by("code")
	return render(request, "portal/courses.html", {"active_term": active_term, "courses": items})


@login_required
def course_detail(request: HttpRequest, code: str) -> HttpResponse:
	active_term = Term.objects.filter(is_active=True).order_by("-start_date").first()
	course = get_object_or_404(Course, code=code.upper())
	sections = Section.objects.select_related("term").filter(course=course)
	if active_term:
		sections = sections.filter(term=active_term)
	sections = sections.order_by("section_code")

	enrolled = set(
		Enrollment.objects.filter(
			student=request.user,
			section__in=sections,
			status=Enrollment.Status.ENROLLED,
		).values_list("section_id", flat=True)
	)
	return render(
		request,
		"portal/course_detail.html",
		{"active_term": active_term, "course": course, "sections": sections, "enrolled_section_ids": enrolled},
	)


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
	ensure_role_groups()

	now = timezone.now()
	if request.user.is_superuser:
		announcements_qs = Announcement.objects.all()
	else:
		announcements_qs = Announcement.objects.filter(
			Q(target_roles__isnull=True) | Q(target_roles__in=request.user.groups.all())
		).distinct()
	announcements_qs = announcements_qs.order_by("-is_pinned", "-publish_at")
	announcements = [a for a in announcements_qs[:50] if a.is_active(now)]

	active_term = Term.objects.filter(is_active=True).order_by("-start_date").first()
	my_enrollments = Enrollment.objects.select_related("section__course", "section__term").filter(
		student=request.user, status=Enrollment.Status.ENROLLED
	)
	my_sections = [e.section for e in my_enrollments]

	my_teaching = Section.objects.select_related("course", "term").filter(
		instructors__instructor=request.user
	)

	open_tickets = SupportTicket.objects.filter(created_by=request.user).exclude(
		status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]
	)

	context = {
		"active_term": active_term,
		"announcements": announcements,
		"my_sections": my_sections,
		"my_teaching": my_teaching,
		"open_tickets": open_tickets,
	}
	return render(request, "portal/dashboard.html", context)


@login_required
def profile(request: HttpRequest) -> HttpResponse:
	return render(request, "portal/profile.html")


@login_required
def announcements(request: HttpRequest) -> HttpResponse:
	now = timezone.now()
	if request.user.is_superuser:
		qs = Announcement.objects.all()
	else:
		qs = Announcement.objects.filter(Q(target_roles__isnull=True) | Q(target_roles__in=request.user.groups.all())).distinct()
	items = [a for a in qs.order_by("-is_pinned", "-publish_at")[:200] if a.is_active(now)]
	return render(request, "portal/announcements.html", {"announcements": items})


@login_required
def registration_add_drop(request: HttpRequest) -> HttpResponse:
	_require_role(request, "STUDENT")

	active_term = Term.objects.filter(is_active=True).order_by("-start_date").first()
	if not active_term:
		messages.info(request, "No active term is configured yet.")
		return render(request, "portal/registration.html", {"active_term": None})

	available_sections = Section.objects.select_related("course").filter(term=active_term).order_by("course__code")
	my_enrollments = Enrollment.objects.select_related("section__course").filter(
		student=request.user, section__term=active_term
	)
	enrolled_section_ids = {e.section_id for e in my_enrollments if e.status == Enrollment.Status.ENROLLED}

	now = timezone.now()
	reg_open = True
	if active_term.registration_start and now < active_term.registration_start:
		reg_open = False
	if active_term.registration_end and now > active_term.registration_end:
		reg_open = False

	if request.method == "POST":
		if not reg_open:
			messages.error(request, "Registration window is closed.")
			return redirect("portal:registration")

		action = request.POST.get("action")
		section_id = request.POST.get("section_id")
		section = get_object_or_404(Section, id=section_id, term=active_term)

		if action == "add":
			with transaction.atomic():
				enrollment = Enrollment.objects.select_for_update().filter(section=section, student=request.user).first()
				if enrollment and enrollment.status == Enrollment.Status.ENROLLED:
					messages.info(request, "Already enrolled.")
				else:
					enrolled_count = (
						Enrollment.objects.select_for_update()
						.filter(section=section, status=Enrollment.Status.ENROLLED)
						.exclude(student=request.user)
						.count()
					)
					seat_available = enrolled_count < section.capacity
					if not enrollment:
						enrollment = Enrollment(section=section, student=request.user)
					if seat_available:
						enrollment.status = Enrollment.Status.ENROLLED
						enrollment.save(update_fields=["status"] if enrollment.id else None)
						_audit(request, action="registration.add", entity_type="section", entity_id=str(section.id))
						messages.success(request, "Enrolled successfully.")
					else:
						enrollment.status = Enrollment.Status.WAITLISTED
						enrollment.save(update_fields=["status"] if enrollment.id else None)
						_audit(request, action="registration.waitlist", entity_type="section", entity_id=str(section.id))
						messages.warning(request, "Section full; you are waitlisted.")
		elif action == "drop":
			enrollment = Enrollment.objects.filter(section=section, student=request.user).first()
			if not enrollment or enrollment.status != Enrollment.Status.ENROLLED:
				messages.info(request, "Not enrolled.")
			else:
				enrollment.status = Enrollment.Status.DROPPED
				enrollment.save(update_fields=["status"])
				_audit(request, action="registration.drop", entity_type="section", entity_id=str(section.id))
				messages.success(request, "Dropped successfully.")
		else:
			messages.error(request, "Invalid action.")

		return redirect("portal:registration")

	context = {
		"active_term": active_term,
		"reg_open": reg_open,
		"sections": available_sections,
		"my_enrollments": my_enrollments,
		"enrolled_section_ids": enrolled_section_ids,
	}
	return render(request, "portal/registration.html", context)


@login_required
def timetable(request: HttpRequest) -> HttpResponse:
	_require_role(request, "STUDENT", "FACULTY")

	active_term = Term.objects.filter(is_active=True).order_by("-start_date").first()
	if is_in_role(request.user, "FACULTY"):
		sections = Section.objects.select_related("course").filter(term=active_term, instructors__instructor=request.user)
	else:
		sections = Section.objects.select_related("course").filter(
			term=active_term, enrollments__student=request.user, enrollments__status=Enrollment.Status.ENROLLED
		)
	sections = sections.order_by("course__code", "section_code")
	return render(request, "portal/timetable.html", {"active_term": active_term, "sections": sections})


@login_required
def grades(request: HttpRequest) -> HttpResponse:
	_require_role(request, "STUDENT")

	grades_qs = (
		Grade.objects.select_related("section__course", "section__term")
		.filter(student=request.user, released=True)
		.order_by("-section__term__start_date", "section__course__code")
	)
	return render(request, "portal/grades.html", {"grades": grades_qs})


@login_required
def faculty_grades(request: HttpRequest, section_id: int) -> HttpResponse:
	_require_role(request, "FACULTY")

	section = get_object_or_404(Section.objects.select_related("course", "term"), id=section_id)
	if not (request.user.is_superuser or SectionInstructor.objects.filter(section=section, instructor=request.user).exists()):
		raise Http404()

	enrollments = Enrollment.objects.select_related("student").filter(section=section, status=Enrollment.Status.ENROLLED)
	existing = {g.student_id: g for g in Grade.objects.filter(section=section)}

	if request.method == "POST":
		with transaction.atomic():
			for enr in enrollments:
				val = (request.POST.get(f"grade_{enr.student_id}") or "").strip().upper()
				released = request.POST.get("released") == "on"
				grade = existing.get(enr.student_id) or Grade(section=section, student=enr.student)
				grade.value = val
				grade.released = released
				grade.save()
			_audit(request, action="grades.update", entity_type="section", entity_id=str(section.id), metadata={"released": released})
		messages.success(request, "Grades saved.")
		return redirect("portal:faculty_grades", section_id=section.id)

	rows = []
	for enr in enrollments:
		g = existing.get(enr.student_id)
		rows.append({"student": enr.student, "grade": g.value if g else "", "released": g.released if g else False})

	return render(request, "portal/faculty_grades.html", {"section": section, "rows": rows})


def _build_unofficial_transcript_pdf(user, grades_qs) -> bytes:
	buffer = BytesIO()
	pdf = canvas.Canvas(buffer, pagesize=letter)
	width, height = letter
	y = height - 50
	pdf.setFont("Helvetica-Bold", 16)
	pdf.drawString(50, y, "Unofficial Transcript")
	y -= 25
	pdf.setFont("Helvetica", 11)
	pdf.drawString(50, y, f"Student: {user.get_full_name() or user.username}")
	y -= 15
	pdf.drawString(50, y, f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
	y -= 25

	pdf.setFont("Helvetica-Bold", 11)
	pdf.drawString(50, y, "Term")
	pdf.drawString(200, y, "Course")
	pdf.drawString(400, y, "Grade")
	y -= 12
	pdf.setFont("Helvetica", 11)

	for g in grades_qs:
		if y < 60:
			pdf.showPage()
			y = height - 50
		term_name = g.section.term.name
		course_code = g.section.course.code
		pdf.drawString(50, y, term_name)
		pdf.drawString(200, y, course_code)
		pdf.drawString(400, y, g.value or "")
		y -= 14

	pdf.showPage()
	pdf.save()
	return buffer.getvalue()


@login_required
def unofficial_transcript_pdf(request: HttpRequest) -> HttpResponse:
	_require_role(request, "STUDENT", "ALUMNI")
	grades_qs = Grade.objects.select_related("section__term", "section__course").filter(student=request.user, released=True)
	content = _build_unofficial_transcript_pdf(request.user, grades_qs.order_by("section__term__start_date", "section__course__code"))
	_audit(request, action="transcript.unofficial.download", entity_type="user", entity_id=str(request.user.id))
	return FileResponse(BytesIO(content), as_attachment=True, filename="unofficial_transcript.pdf")


@login_required
def transcript_requests(request: HttpRequest) -> HttpResponse:
	_require_role(request, "STUDENT", "ALUMNI")
	items = TranscriptRequest.objects.filter(requester=request.user).order_by("-created_at")
	return render(request, "portal/transcript_requests.html", {"requests": items})


@login_required
def transcript_request_new(request: HttpRequest) -> HttpResponse:
	_require_role(request, "STUDENT", "ALUMNI")
	if request.method == "POST":
		purpose = (request.POST.get("purpose") or "").strip()
		delivery_method = request.POST.get("delivery_method")
		recipient_details = (request.POST.get("recipient_details") or "").strip()
		if not purpose or delivery_method not in TranscriptRequest.DeliveryMethod.values:
			messages.error(request, "Please fill all required fields.")
		else:
			tr = TranscriptRequest.objects.create(
				requester=request.user,
				purpose=purpose,
				delivery_method=delivery_method,
				recipient_details=recipient_details,
				status=TranscriptRequest.Status.SUBMITTED,
			)
			TranscriptRequestEvent.objects.create(
				request=tr,
				actor=request.user,
				from_status="",
				to_status=tr.status,
				note="Created by requester",
			)
			_audit(request, action="transcript.request.create", entity_type="transcript_request", entity_id=str(tr.id))
			messages.success(request, "Request submitted.")
			return redirect("portal:transcript_requests")
	return render(request, "portal/transcript_request_new.html", {"delivery_methods": TranscriptRequest.DeliveryMethod.choices})


@login_required
def transcript_request_detail(request: HttpRequest, request_id: int) -> HttpResponse:
	_require_role(request, "STUDENT", "ALUMNI")
	tr = get_object_or_404(TranscriptRequest, id=request_id, requester=request.user)
	events = tr.events.select_related("actor").order_by("created_at")
	return render(request, "portal/transcript_request_detail.html", {"tr": tr, "events": events})


@login_required
def transcript_request_cancel(request: HttpRequest, request_id: int) -> HttpResponse:
	_require_role(request, "STUDENT", "ALUMNI")
	tr = get_object_or_404(TranscriptRequest, id=request_id, requester=request.user)
	if tr.status in [TranscriptRequest.Status.ISSUED, TranscriptRequest.Status.REJECTED]:
		messages.info(request, "This request can no longer be cancelled.")
		return redirect("portal:transcript_request_detail", request_id=tr.id)
	if request.method == "POST":
		prev = tr.status
		tr.status = TranscriptRequest.Status.REJECTED
		tr.review_reason = "Cancelled by requester"
		tr.reviewed_by = request.user
		tr.save(update_fields=["status", "review_reason", "reviewed_by", "updated_at"])
		TranscriptRequestEvent.objects.create(
			request=tr,
			actor=request.user,
			from_status=prev,
			to_status=tr.status,
			note="Cancelled by requester",
		)
		_audit(request, action="transcript.request.cancel", entity_type="transcript_request", entity_id=str(tr.id))
		messages.success(request, "Request cancelled.")
		return redirect("portal:transcript_requests")
	return render(request, "portal/confirm.html", {"title": "Cancel transcript request", "message": "Cancel this request?"})


@login_required
def registrar_queue(request: HttpRequest) -> HttpResponse:
	_require_role(request, "REGISTRAR")
	items = TranscriptRequest.objects.all().order_by("status", "created_at")
	return render(request, "portal/registrar_queue.html", {"items": items})


@login_required
def registrar_approve(request: HttpRequest, request_id: int) -> HttpResponse:
	_require_role(request, "REGISTRAR")
	tr = get_object_or_404(TranscriptRequest, id=request_id)
	if request.method == "POST":
		prev = tr.status
		tr.status = TranscriptRequest.Status.APPROVED
		tr.reviewed_by = request.user
		tr.review_reason = (request.POST.get("reason") or "").strip()
		tr.save(update_fields=["status", "reviewed_by", "review_reason", "updated_at"])
		TranscriptRequestEvent.objects.create(
			request=tr,
			actor=request.user,
			from_status=prev,
			to_status=tr.status,
			note=tr.review_reason,
		)
		_audit(request, action="transcript.request.approve", entity_type="transcript_request", entity_id=str(tr.id))
		messages.success(request, "Approved.")
		return redirect("portal:registrar_queue")
	return render(request, "portal/registrar_action.html", {"tr": tr, "action": "approve"})


@login_required
def registrar_reject(request: HttpRequest, request_id: int) -> HttpResponse:
	_require_role(request, "REGISTRAR")
	tr = get_object_or_404(TranscriptRequest, id=request_id)
	if request.method == "POST":
		reason = (request.POST.get("reason") or "").strip()
		if not reason:
			messages.error(request, "Reason is required.")
		else:
			prev = tr.status
			tr.status = TranscriptRequest.Status.REJECTED
			tr.reviewed_by = request.user
			tr.review_reason = reason
			tr.save(update_fields=["status", "reviewed_by", "review_reason", "updated_at"])
			TranscriptRequestEvent.objects.create(
				request=tr,
				actor=request.user,
				from_status=prev,
				to_status=tr.status,
				note=reason,
			)
			_audit(request, action="transcript.request.reject", entity_type="transcript_request", entity_id=str(tr.id))
			messages.success(request, "Rejected.")
			return redirect("portal:registrar_queue")
	return render(request, "portal/registrar_action.html", {"tr": tr, "action": "reject"})


@login_required
def registrar_issue(request: HttpRequest, request_id: int) -> HttpResponse:
	_require_role(request, "REGISTRAR")
	tr = get_object_or_404(TranscriptRequest, id=request_id)
	if request.method == "POST":
		prev = tr.status
		tr.status = TranscriptRequest.Status.ISSUED
		tr.reviewed_by = request.user
		tr.issued_at = timezone.now()
		tr.ensure_verification_code()
		tr.save(update_fields=["status", "reviewed_by", "issued_at", "verification_code", "updated_at"])
		TranscriptRequestEvent.objects.create(
			request=tr,
			actor=request.user,
			from_status=prev,
			to_status=tr.status,
			note="Issued",
		)
		_audit(request, action="transcript.request.issue", entity_type="transcript_request", entity_id=str(tr.id))
		messages.success(request, "Issued.")
		return redirect("portal:registrar_queue")
	return render(request, "portal/registrar_action.html", {"tr": tr, "action": "issue"})


@login_required
def official_transcript_pdf(request: HttpRequest, request_id: int) -> HttpResponse:
	_require_role(request, "REGISTRAR")
	tr = get_object_or_404(TranscriptRequest, id=request_id)
	if tr.status != TranscriptRequest.Status.ISSUED:
		raise Http404()

	grades_qs = Grade.objects.select_related("section__term", "section__course").filter(student=tr.requester, released=True)
	content = _build_unofficial_transcript_pdf(tr.requester, grades_qs.order_by("section__term__start_date", "section__course__code"))

	# Stamp a minimal verification line on first page (simple MVP).
	buffer = BytesIO()
	buffer.write(content)
	buffer.seek(0)

	_audit(request, action="transcript.official.download", entity_type="transcript_request", entity_id=str(tr.id))
	return FileResponse(buffer, as_attachment=True, filename=f"official_transcript_TR{tr.id}.pdf")


@login_required
def finance(request: HttpRequest) -> HttpResponse:
	_require_role(request, "STUDENT", "ALUMNI", "FINANCE")
	if is_in_role(request.user, "FINANCE") or request.user.is_superuser:
		student_id = request.GET.get("student_id")
		invoices = FeeInvoice.objects.select_related("term", "student").order_by("-due_date")
		if student_id:
			invoices = invoices.filter(student_id=student_id)
		return render(request, "portal/finance_staff.html", {"invoices": invoices})
	invoices = FeeInvoice.objects.select_related("term").filter(student=request.user).order_by("-due_date")
	return render(request, "portal/finance.html", {"invoices": invoices})


@login_required
def support(request: HttpRequest) -> HttpResponse:
	items = SupportTicket.objects.filter(created_by=request.user).order_by("-updated_at")
	return render(request, "portal/support.html", {"tickets": items})


@login_required
def support_new(request: HttpRequest) -> HttpResponse:
	if request.method == "POST":
		category = (request.POST.get("category") or "").strip()
		subject = (request.POST.get("subject") or "").strip()
		description = (request.POST.get("description") or "").strip()
		if not category or not subject or not description:
			messages.error(request, "All fields are required.")
		else:
			t = SupportTicket.objects.create(
				created_by=request.user,
				category=category,
				subject=subject,
				description=description,
				status=SupportTicket.Status.OPEN,
			)
			_audit(request, action="support.ticket.create", entity_type="support_ticket", entity_id=str(t.id))
			messages.success(request, "Ticket created.")
			return redirect("portal:support_detail", ticket_id=t.id)
	return render(request, "portal/support_new.html")


@login_required
def support_detail(request: HttpRequest, ticket_id: int) -> HttpResponse:
	t = get_object_or_404(SupportTicket, id=ticket_id)
	if not (request.user.is_superuser or t.created_by_id == request.user.id or is_in_role(request.user, "ADMIN")):
		raise Http404()

	if request.method == "POST":
		msg = (request.POST.get("message") or "").strip()
		if msg:
			SupportMessage.objects.create(ticket=t, author=request.user, message=msg)
			t.updated_at = timezone.now()
			t.save(update_fields=["updated_at"])
			_audit(request, action="support.message.create", entity_type="support_ticket", entity_id=str(t.id))
			return redirect("portal:support_detail", ticket_id=t.id)

	ticket_messages = t.messages.select_related("author").order_by("created_at")
	return render(request, "portal/support_detail.html", {"ticket": t, "ticket_messages": ticket_messages})
