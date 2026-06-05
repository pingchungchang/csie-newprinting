from django.urls import path

from .views import (
    AdminAddUserView,
    AdminJobDetailView,
    AdminJobsView,
    AdminMeView,
    AdminRemoveUserView,
    AdminTransferView,
    AdminUserView,
    JobDetailView,
    JobListView,
    LoginView,
    MeView,
    PrintView,
)

urlpatterns = [
    path("login", LoginView.as_view(), name="api-login"),
    path("me", MeView.as_view(), name="api-me"),
    path("print", PrintView.as_view(), name="api-print"),
    path("jobs", JobListView.as_view(), name="api-jobs"),
    path("jobs/<str:jobId>", JobDetailView.as_view(), name="api-job-detail"),
    path("admin/me", AdminMeView.as_view(), name="api-admin-me"),
    path("admin/jobs", AdminJobsView.as_view(), name="api-admin-jobs"),
    path(
        "admin/jobs/<str:jobId>",
        AdminJobDetailView.as_view(),
        name="api-admin-job-detail",
    ),
    path("admin/transfer", AdminTransferView.as_view(), name="api-admin-transfer"),
    path("admin/adduser", AdminAddUserView.as_view(), name="api-admin-adduser"),
    path("admin/removeuser", AdminRemoveUserView.as_view(), name="api-admin-removeuser"),
    path("admin/user", AdminUserView.as_view(), name="api-admin-user"),
]
