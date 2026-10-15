from django.contrib import admin

from .models import Appointment, Department, Diagnosis, Doctor, Patient


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "floor")


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialty", "department", "cabinet", "experience")
    list_filter = ("department", "specialty")
    search_fields = ("full_name", "specialty")
    ordering = ("full_name",)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "birth_date", "phone")
    search_fields = ("full_name", "phone")


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ("code", "title")
    search_fields = ("code", "title")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Расширенная настройка Admin для основной модели."""
    list_display = ("date", "time", "patient", "doctor", "status", "price")
    list_filter = ("status", "doctor__department", "date")
    search_fields = ("patient__full_name", "doctor__full_name", "complaints")
    ordering = ("-date", "time")
    date_hierarchy = "date"
    list_editable = ("status",)
    filter_horizontal = ("diagnoses",)
    list_select_related = ("patient", "doctor")
    list_per_page = 20
