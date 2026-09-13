from django.urls import path

from .views import ChangePasswordView, ExportDataView, MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("me/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("me/export/", ExportDataView.as_view(), name="export-data"),
]
