from django.urls import path

from . import views

app_name = "clinic"
urlpatterns = [
    path("", views.index, name="index"),
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/create/", views.appointment_create, name="appointment_create"),
    path("appointments/<int:pk>/", views.AppointmentDetailView.as_view(), name="appointment_detail"),
    path("appointments/<int:pk>/edit/", views.AppointmentUpdateView.as_view(), name="appointment_edit"),
    path("appointments/<int:pk>/delete/", views.AppointmentDeleteView.as_view(), name="appointment_delete"),
    path("doctors/<int:pk>/", views.doctor_detail, name="doctor_detail"),
    path("statistics/", views.statistics, name="statistics"),
]
