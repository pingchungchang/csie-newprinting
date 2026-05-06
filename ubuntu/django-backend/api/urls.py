from django.urls import path

from .views import AdminView, JobDetailView, JobListView, LoginView, MeView, PrintView

urlpatterns = [
    path("login", LoginView.as_view(), name="api-login"),
    path("me", MeView.as_view(), name="api-me"),
    path("print", PrintView.as_view(), name="api-print"),
    path("jobs", JobListView.as_view(), name="api-jobs"),
    path("jobs/<str:jobId>", JobDetailView.as_view(), name="api-job-detail"),
    path("admin", AdminView.as_view(), name="api-admin"),
]
