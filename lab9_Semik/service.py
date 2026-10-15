"""Бизнес-логика страховой компании."""
from exceptions import ValidationError
from models import INSURANCE_TYPES, STATUSES, Policy
from repository import PolicyRepository

EDITABLE = {"holder", "insurance_type", "insured_value", "term_months", "status"}


class PolicyService:
    def __init__(self, repository: PolicyRepository) -> None:
        self.repository = repository

    @staticmethod
    def _validate(data: dict, partial: bool = False) -> dict:
        unknown = set(data) - EDITABLE
        if unknown:
            raise ValidationError(f"Unknown fields: {', '.join(sorted(unknown))}")
        if not partial:
            missing = {"holder", "insurance_type", "insured_value", "term_months"} - set(data)
            if missing:
                raise ValidationError(f"Missing fields: {', '.join(sorted(missing))}")
        result = dict(data)
        if "holder" in result and not str(result["holder"]).strip():
            raise ValidationError("holder must not be empty")
        if "insurance_type" in result and result["insurance_type"] not in INSURANCE_TYPES:
            raise ValidationError(f"insurance_type must be one of {sorted(INSURANCE_TYPES)}")
        if "status" in result and result["status"] not in STATUSES:
            raise ValidationError(f"status must be one of {sorted(STATUSES)}")
        try:
            if "insured_value" in result:
                result["insured_value"] = float(result["insured_value"])
                if result["insured_value"] <= 0:
                    raise ValidationError("insured_value must be > 0")
            if "term_months" in result:
                result["term_months"] = int(result["term_months"])
                if not 1 <= result["term_months"] <= 60:
                    raise ValidationError("term_months must be in [1; 60]")
        except (TypeError, ValueError) as error:
            raise ValidationError(f"Invalid numeric value: {error}") from error
        return result

    def list_policies(self, insurance_type: str | None = None) -> list[Policy]:
        policies = self.repository.get_all()
        if insurance_type:
            policies = [p for p in policies if p.insurance_type == insurance_type]
        return policies

    def get(self, policy_id: int) -> Policy:
        return self.repository.get(int(policy_id))

    def create(self, data: dict) -> Policy:
        return self.repository.add(self._validate(data))

    def update(self, policy_id: int, data: dict) -> Policy:
        if not data:
            raise ValidationError("Nothing to update")
        return self.repository.update(int(policy_id), self._validate(data, partial=True))

    def delete(self, policy_id: int) -> None:
        self.repository.delete(int(policy_id))

    def calculate_cost(self, policy_id: int, driver_experience: int | None = None,
                       claims: int = 0) -> dict:
        """Специализированная операция варианта: расчёт стоимости полиса."""
        policy = self.get(policy_id)
        rate = INSURANCE_TYPES[policy.insurance_type]
        base = policy.insured_value * rate * policy.term_months / 12
        coefficient = 1.0 + 0.15 * max(0, int(claims))
        if policy.insurance_type == "auto" and driver_experience is not None:
            coefficient *= 1.5 if int(driver_experience) < 3 else 1.0
        cost = round(base * coefficient, 2)
        return {"policy_id": policy.id, "base_rate": rate, "coefficient": round(coefficient, 3),
                "cost": cost, "monthly": round(cost / policy.term_months, 2)}
