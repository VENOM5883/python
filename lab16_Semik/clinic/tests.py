from datetime import date, time

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .forms import AppointmentForm
from .models import Appointment, Doctor


class ClinicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", stdout=open("/dev/null", "w"))

    def login_user(self):
        self.client.login(username="user", password="user12345")

    def login_admin(self):
        self.client.login(username="admin", password="admin12345")

    def test_01_index(self):
        response = self.client.get(reverse("clinic:index"))
        self.assertContains(response, "Приёмов: <b>30</b>", html=False)

    def test_02_list_requires_login(self):
        self.assertEqual(self.client.get(reverse("clinic:appointment_list")).status_code, 302)

    def test_03_list_and_pagination(self):
        self.login_user()
        response = self.client.get(reverse("clinic:appointment_list"))
        self.assertEqual(len(response.context["page"]), 10)
        self.assertEqual(response.context["page"].paginator.num_pages, 3)
        self.assertEqual(len(self.client.get(reverse("clinic:appointment_list") + "?page=3").context["page"]), 10)

    def test_04_detail(self):
        self.login_user()
        appointment = Appointment.objects.first()
        response = self.client.get(appointment.get_absolute_url())
        self.assertContains(response, appointment.patient.full_name)

    def test_05_search(self):
        self.login_user()
        response = self.client.get(reverse("clinic:appointment_list"), {"q": "Кузнецов"})
        self.assertTrue(all(a.doctor.full_name.startswith("Кузнецов") for a in response.context["page"]))
        self.assertEqual(response.context["page"].paginator.count, 6)

    def test_06_filter(self):
        self.login_user()
        response = self.client.get(reverse("clinic:appointment_list"), {"status": "completed", "department": 2})
        items = list(response.context["page"])
        self.assertTrue(items and all(a.status == "completed" and a.doctor.department_id == 2 for a in items))

    def test_07_sort(self):
        self.login_user()
        response = self.client.get(reverse("clinic:appointment_list"), {"sort": "-price"})
        prices = [a.price for a in response.context["page"]]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_08_user_cannot_create(self):
        self.login_user()
        self.assertEqual(self.client.get(reverse("clinic:appointment_create")).status_code, 403)
        self.assertEqual(self.client.post(reverse("clinic:appointment_delete", args=[1])).status_code, 403)

    def test_09_admin_create(self):
        self.login_admin()
        data = {"patient": 1, "doctor": 1, "date": "2026-11-01", "time": "10:00", "status": "planned", "price": "1500"}
        response = self.client.post(reverse("clinic:appointment_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Appointment.objects.filter(date=date(2026, 11, 1)).exists())

    def test_10_admin_edit(self):
        self.login_admin()
        appointment = Appointment.objects.filter(status="planned").first()
        data = {"patient": appointment.patient_id, "doctor": appointment.doctor_id, "date": appointment.date,
                "time": appointment.time.strftime("%H:%M"), "status": "confirmed", "price": "2500"}
        self.client.post(reverse("clinic:appointment_edit", args=[appointment.pk]), data)
        appointment.refresh_from_db()
        self.assertEqual((appointment.status, int(appointment.price)), ("confirmed", 2500))

    def test_11_admin_delete(self):
        self.login_admin()
        self.client.post(reverse("clinic:appointment_delete", args=[1]))
        self.assertFalse(Appointment.objects.filter(pk=1).exists())

    def test_12_validation(self):
        busy = Appointment.objects.first()
        form = AppointmentForm({"patient": 1, "doctor": busy.doctor_id, "date": busy.date,
                                "time": busy.time.strftime("%H:%M"), "status": "completed", "price": "-5"})
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)
        self.assertTrue(form.non_field_errors())

    def test_13_statistics(self):
        self.login_user()
        response = self.client.get(reverse("clinic:statistics"))
        self.assertEqual(response.context["totals"]["total"], 30)

    def test_14_relations(self):
        doctor = Doctor.objects.get(full_name__startswith="Кузнецов")
        self.assertEqual(doctor.appointments.count(), 6)
        self.assertEqual(doctor.department.name, "Кардиологическое")
        completed = Appointment.objects.filter(status="completed").first()
        self.assertGreaterEqual(completed.diagnoses.count(), 1)

    def test_15_auth_and_admin_panel(self):
        self.assertFalse(User.objects.get(username="user").check_password("wrong"))
        self.login_admin()
        self.assertEqual(self.client.get("/admin/clinic/appointment/").status_code, 200)

    def test_16_unique_slot(self):
        busy = Appointment.objects.first()
        form = AppointmentForm({"patient": 2, "doctor": busy.doctor_id, "date": busy.date,
                                "time": busy.time.strftime("%H:%M"), "status": "planned", "price": "100"})
        self.assertFalse(form.is_valid())

    def test_17_nplus1_command(self):
        from io import StringIO
        out = StringIO()
        call_command("nplus1", stdout=out)
        self.assertIn("select_related: 1", out.getvalue())
