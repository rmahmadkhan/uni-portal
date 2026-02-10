from django.contrib import admin

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


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
	list_display = ("name", "start_date", "end_date", "is_active")
	list_filter = ("is_active",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
	list_display = ("code", "title", "department", "credits")
	search_fields = ("code", "title")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
	list_display = ("term", "course", "section_code", "capacity", "meeting_days", "location")
	list_filter = ("term",)
	search_fields = ("course__code", "course__title")


@admin.register(SectionInstructor)
class SectionInstructorAdmin(admin.ModelAdmin):
	list_display = ("section", "instructor")
	list_filter = ("section__term",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
	list_display = ("section", "student", "status", "created_at")
	list_filter = ("status", "section__term")
	search_fields = ("student__username", "student__email", "section__course__code")


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
	list_display = ("section", "student", "value", "released", "updated_at")
	list_filter = ("released", "section__term")
	search_fields = ("student__username", "section__course__code")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
	list_display = ("title", "created_by", "publish_at", "expire_at", "is_pinned")
	list_filter = ("is_pinned",)
	search_fields = ("title", "body")


@admin.register(FeeInvoice)
class FeeInvoiceAdmin(admin.ModelAdmin):
	list_display = ("reference_no", "student", "term", "amount", "due_date", "status")
	list_filter = ("status", "term")
	search_fields = ("reference_no", "student__username", "student__email")


@admin.register(TranscriptRequest)
class TranscriptRequestAdmin(admin.ModelAdmin):
	list_display = ("id", "requester", "status", "delivery_method", "created_at", "issued_at")
	list_filter = ("status", "delivery_method")
	search_fields = ("requester__username", "requester__email")


@admin.register(TranscriptRequestEvent)
class TranscriptRequestEventAdmin(admin.ModelAdmin):
	list_display = ("request", "actor", "from_status", "to_status", "created_at")
	list_filter = ("to_status",)


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
	list_display = ("id", "created_by", "category", "subject", "status", "assigned_to", "updated_at")
	list_filter = ("status", "category")
	search_fields = ("subject", "created_by__username", "created_by__email")


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
	list_display = ("ticket", "author", "created_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ("created_at", "actor", "action", "entity_type", "entity_id", "ip")
	list_filter = ("action", "entity_type")
	search_fields = ("entity_id", "actor__username", "actor__email")
