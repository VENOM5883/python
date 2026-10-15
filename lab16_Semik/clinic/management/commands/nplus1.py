"""Демонстрация проблемы N+1: python manage.py nplus1"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import CaptureQueriesContext

from clinic.models import Appointment


class Command(BaseCommand):
    def handle(self, *args, **options):
        with CaptureQueriesContext(connection) as bad:
            for a in Appointment.objects.all():
                _ = (a.patient.full_name, a.doctor.full_name, a.doctor.department.name)
        with CaptureQueriesContext(connection) as good:
            for a in Appointment.objects.select_related("patient", "doctor__department"):
                _ = (a.patient.full_name, a.doctor.full_name, a.doctor.department.name)
        with CaptureQueriesContext(connection) as m2m:
            for a in Appointment.objects.prefetch_related("diagnoses"):
                _ = list(a.diagnoses.all())
        self.stdout.write(f"Без оптимизации: {len(bad)} SQL-запросов (1 + N×3)")
        self.stdout.write(f"select_related: {len(good)} SQL-запрос (JOIN)")
        self.stdout.write(f"prefetch_related для M2M: {len(m2m)} SQL-запроса")
