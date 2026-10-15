from django import forms

from .models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "date", "time", "status", "price", "complaints", "diagnoses"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}),
                   "time": forms.TimeInput(attrs={"type": "time"}),
                   "complaints": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned = super().clean()
        status, diagnoses = cleaned.get("status"), cleaned.get("diagnoses")
        if status == Appointment.Status.COMPLETED and not diagnoses:
            raise forms.ValidationError("Для завершённого приёма укажите хотя бы один диагноз")
        return cleaned
