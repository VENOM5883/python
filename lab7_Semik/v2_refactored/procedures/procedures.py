"""Конкретные виды приёма."""
from interfaces.services import Procedure


class TherapyProcedure(Procedure):
    code, title = "therapy", "Терапевтический приём"

    def perform(self, patient_name: str) -> str:
        return f"Осмотр пациента {patient_name} проведён, назначено лечение"

    def price(self) -> float:
        return 1500.0


class DiagnosticsProcedure(Procedure):
    code, title = "diagnostics", "Диагностическая процедура"

    def perform(self, patient_name: str) -> str:
        return f"Диагностика пациента {patient_name} проведена, результаты через 2 дня"

    def price(self) -> float:
        return 3000.0


class ConsultationProcedure(Procedure):
    code, title = "consultation", "Консультация"

    def perform(self, patient_name: str) -> str:
        return f"Консультация пациента {patient_name} проведена"

    def price(self) -> float:
        return 1000.0


class VaccinationProcedure(Procedure):
    """Добавлен после рефакторинга — сервис не менялся (демонстрация OCP)."""
    code, title = "vaccination", "Вакцинация"

    def perform(self, patient_name: str) -> str:
        return f"Пациенту {patient_name} проведена вакцинация"

    def price(self) -> float:
        return 800.0


ALL_PROCEDURES: dict[str, Procedure] = {p.code: p for p in (
    TherapyProcedure(), DiagnosticsProcedure(), ConsultationProcedure(), VaccinationProcedure())}
