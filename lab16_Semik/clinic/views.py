from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, UpdateView

from .forms import AppointmentForm
from .models import Appointment, Department, Doctor, Patient

SORTS = {"date": ("-date", "time"), "-date": ("date", "time"), "patient": ("patient__full_name",),
         "doctor": ("doctor__full_name",), "price": ("price",), "-price": ("-price",)}


def index(request):
    """FBV: главная страница."""
    context = {"counts": {"Приёмов": Appointment.objects.count(), "Пациентов": Patient.objects.count(),
                          "Врачей": Doctor.objects.count(), "Отделений": Department.objects.count()}}
    return render(request, "clinic/index.html", context)


@login_required
def appointment_list(request):
    """FBV: список с поиском, фильтрами, сортировкой и пагинацией (всё на стороне БД)."""
    queryset = Appointment.objects.select_related("patient", "doctor", "doctor__department")
    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(Q(patient__full_name__icontains=query) |
                                   Q(doctor__full_name__icontains=query) | Q(complaints__icontains=query))
    if request.GET.get("status"):
        queryset = queryset.filter(status=request.GET["status"])
    if request.GET.get("department"):
        queryset = queryset.filter(doctor__department_id=request.GET["department"])
    if request.GET.get("hide_cancelled"):
        queryset = queryset.exclude(status=Appointment.Status.CANCELLED)
    sort = request.GET.get("sort", "date")
    queryset = queryset.order_by(*SORTS.get(sort, SORTS["date"]))
    page = Paginator(queryset, 10).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "clinic/appointment_list.html", {
        "page": page, "statuses": Appointment.Status.choices, "departments": Department.objects.all(),
        "sort": sort, "query_string": params.urlencode()})


class AppointmentDetailView(DetailView):
    """CBV: детальная страница."""
    model = Appointment
    template_name = "clinic/appointment_detail.html"

    def get_queryset(self):
        return (Appointment.objects.select_related("patient", "doctor__department")
                .prefetch_related("diagnoses"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["history"] = (self.object.patient.appointments.select_related("doctor")
                              .exclude(pk=self.object.pk).order_by("-date")[:5])
        return context


@permission_required("clinic.add_appointment", raise_exception=True)
def appointment_create(request):
    """FBV: создание (только администратор)."""
    form = AppointmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        appointment = form.save()
        messages.success(request, "Запись создана")
        return redirect(appointment)
    return render(request, "clinic/appointment_form.html", {"form": form, "title": "Новая запись"})


class AppointmentUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    """CBV: редактирование."""
    model = Appointment
    form_class = AppointmentForm
    template_name = "clinic/appointment_form.html"
    permission_required = "clinic.change_appointment"
    raise_exception = True
    success_message = "Изменения сохранены"
    extra_context = {"title": "Редактирование записи"}


class AppointmentDeleteView(PermissionRequiredMixin, DeleteView):
    """CBV: удаление с подтверждением."""
    model = Appointment
    template_name = "clinic/appointment_confirm_delete.html"
    permission_required = "clinic.delete_appointment"
    raise_exception = True
    success_url = reverse_lazy("clinic:appointment_list")

    def form_valid(self, form):
        messages.success(self.request, "Запись удалена")
        return super().form_valid(form)


@login_required
def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor.objects.select_related("department"), pk=pk)
    appointments = doctor.appointments.select_related("patient").order_by("-date", "time")[:20]
    return render(request, "clinic/doctor_detail.html", {"doctor": doctor, "appointments": appointments})


@login_required
def statistics(request):
    """Статистика средствами ORM: aggregate, annotate, count, exists."""
    totals = Appointment.objects.aggregate(total=Count("id"), avg_price=Avg("price"),
                                           revenue=Sum("price", filter=Q(status="completed")))
    by_department = (Department.objects.annotate(appointments=Count("doctors__appointments"))
                     .order_by("-appointments"))
    by_status = Appointment.objects.values("status").annotate(count=Count("id")).order_by("-count")
    top_doctors = Doctor.objects.annotate(n=Count("appointments")).order_by("-n")[:3]
    return render(request, "clinic/statistics.html", {
        "totals": totals, "by_department": by_department, "top_doctors": top_doctors,
        "by_status": [(Appointment.Status(row["status"]).label, row["count"]) for row in by_status],
        "has_cancelled": Appointment.objects.filter(status="cancelled").exists()})
