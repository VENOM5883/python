from dataclasses import asdict, dataclass

INSURANCE_TYPES = {"auto": 0.045, "property": 0.012, "travel": 0.03, "health": 0.06}
STATUSES = {"draft", "active", "expired", "cancelled"}


@dataclass
class Policy:
    id: int
    holder: str
    insurance_type: str
    insured_value: float
    term_months: int
    status: str = "draft"

    def to_dict(self) -> dict:
        return asdict(self)
