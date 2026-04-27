from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Literal


class UntilAge(BaseModel):
    age: int

class UntilYear(BaseModel):
    year: int

class Segment(BaseModel):
    value: float
    until: UntilAge | UntilYear | None = None  # None = indefinite
    one_off: bool = False

class LineItem(BaseModel):
    label: str
    segments: list[Segment]

class Expenses(BaseModel):
    fixed: list[LineItem] = []
    variable: list[LineItem] = []
    guilt_free: list[LineItem] = []
    savings: list[LineItem] = []
    investments: list[LineItem] = []

class Allocation(BaseModel):
    equities: float
    bonds: float
    cash: float
    other: float

    @field_validator('equities', 'bonds', 'cash', 'other')
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError('allocation weights must be non-negative')
        return v

class Profile(BaseModel):
    current_age: int
    current_net_worth: float

class PlanRequest(BaseModel):
    profile: Profile
    goals: list[LineItem] = []
    income: list[Segment] = []
    expenses: Expenses = Expenses()
    remainder_to: Literal['fixed', 'variable', 'guilt_free', 'savings', 'investments'] = 'investments'
    allocation: Allocation

class AgeQuantiles(BaseModel):
    age: int
    p1: float; p5: float; p10: float; p25: float; p50: float
    p75: float; p90: float; p95: float; p99: float

class SimulationResult(BaseModel):
    by_age: list[AgeQuantiles]
    ruin_probability: float

class FieldError(BaseModel):
    field: str
    message: str

class ValidationResponse(BaseModel):
    errors: list[FieldError]
