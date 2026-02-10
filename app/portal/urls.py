from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("healthz/", views.healthz, name="healthz"),
    path("login/", views.PortalLoginView.as_view(), name="login"),
    path("logout/", views.PortalLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),

    path("it/users/new/", views.admin_users_new, name="admin_users_new"),

    path("courses/", views.courses, name="courses"),
    path("courses/<str:code>/", views.course_detail, name="course_detail"),

    path("announcements/", views.announcements, name="announcements"),

    path("registration/", views.registration_add_drop, name="registration"),

    path("timetable/", views.timetable, name="timetable"),

    path("grades/", views.grades, name="grades"),
    path("faculty/grades/section/<int:section_id>/", views.faculty_grades, name="faculty_grades"),

    path("transcripts/", views.transcript_requests, name="transcript_requests"),
    path("transcripts/unofficial.pdf", views.unofficial_transcript_pdf, name="unofficial_transcript_pdf"),
    path("transcripts/request/new/", views.transcript_request_new, name="transcript_request_new"),
    path("transcripts/request/<int:request_id>/", views.transcript_request_detail, name="transcript_request_detail"),
    path("transcripts/request/<int:request_id>/cancel/", views.transcript_request_cancel, name="transcript_request_cancel"),
    path("transcripts/request/<int:request_id>/official.pdf", views.official_transcript_pdf, name="official_transcript_pdf"),

    path("registrar/queue/", views.registrar_queue, name="registrar_queue"),
    path("registrar/queue/<int:request_id>/approve/", views.registrar_approve, name="registrar_approve"),
    path("registrar/queue/<int:request_id>/reject/", views.registrar_reject, name="registrar_reject"),
    path("registrar/queue/<int:request_id>/issue/", views.registrar_issue, name="registrar_issue"),

    path("finance/", views.finance, name="finance"),

    path("support/", views.support, name="support"),
    path("support/new/", views.support_new, name="support_new"),
    path("support/<int:ticket_id>/", views.support_detail, name="support_detail"),
]
