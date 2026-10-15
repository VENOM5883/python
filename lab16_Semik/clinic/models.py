from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse


class Department(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    floor = models.PositiveSmallIntegerField("Этаж", validators=[MinValueValidator(1), MaxValueValidator(10)])

    class Meta:
        ordering = ["name"]
        verbose_name = "Отделение"
        verbose_name_plural = "Отделения"

    def __str__(self):
        return self.name


class Doctor(models.Model):
    full_name = models.CharField("ФИО", max_length=150)
    specialty = models.CharField("Специальность", max_length=80)
    cabinet = models.PositiveIntegerField("Кабинет")
    experience = models.PositiveSmallIntegerField("Стаж, лет", default=0)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="doctors",
                                   verbose_name="Отделение")

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"

    def __str__(self):
        return f"{self.full_name} ({self.specialty})"


class Patient(models.Model):
    full_name = models.CharField("ФИО", max_length=150)
    birth_date = models.DateField("Дата рождения")
    phone = models.CharField("Телефон", max_length=16, unique=True,
                             validators=[RegexValidator(r"^\+7\d{10}$", "Формат: +7XXXXXXXXXX")])

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"

    def __str__(self):
        return self.full_name


class Diagnosis(models.Model):
    code = models.CharField("Код МКБ-10", max_length=10, unique=True)
    title = models.CharField("Наименование", max_length=200)

    class Meta:
        ordering = ["code"]
        verbose_name = "Диагноз"
        verbose_name_plural = "Диагнозы"

    def __str__(self):
        return f"{self.code} {self.title}"


class Appointment(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Запланирован"
        CONFIRMED = "confirmed", "Подтверждён"
        COMPLETED = "completed", "Завершён"
        CANCELLED = "cancelled", "Отменён"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments",
                                verbose_name="Пациент")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments",
                               verbose_name="Врач")
    date = models.DateField("Дата")
    time = models.TimeField("Время")
    status = models.CharField("Статус", max_length=10, choices=Status.choices, default=Status.PLANNED)
    price = models.DecimalField("Стоимость", max_digits=8, decimal_places=2, default=1500,
                                validators=[MinValueValidator(0)])
    complaints = models.TextField("Жалобы", blank=True)
    diagnoses = models.ManyToManyField(Diagnosis, blank=True, related_name="appointments",
                                       verbose_name="Диагнозы")

    class Meta:
        ordering = ["-date", "time"]
        verbose_name = "Приём"
        verbose_name_plural = "Приёмы"
        constraints = [models.UniqueConstraint(fields=["doctor", "date", "time"], name="unique_doctor_slot")]

    def __str__(self):
        return f"{self.date:%d.%m.%Y} {self.time:%H:%M} — {self.patient} у {self.doctor.full_name}"

    def get_absolute_url(self):
        return reverse("clinic:appointment_detail", args=[self.pk])
