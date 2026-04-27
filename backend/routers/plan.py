from fastapi import APIRouter, HTTPException
from models.plan import (
    PlanRequest, SimulationResult, AgeQuantiles,
    ValidationResponse, FieldError, Allocation
)
from services.cashflow import compute_net_cash_flows, HORIZON_YEARS

router = APIRouter(prefix="/api")

RETURN_ASSUMPTIONS = [
    (0.07, 0.15),   # equities
    (0.03, 0.05),   # bonds
    (0.005, 0.005), # cash
    (0.05, 0.10),   # other
]
NUM_PATHS = 10_000


def _validate_allocation(alloc: Allocation) -> list[FieldError]:
    errors = []
    total = alloc.equities + alloc.bonds + alloc.cash + alloc.other
    if abs(total - 100.0) > 0.01:
        errors.append(FieldError(field="allocation", message=f"Weights must sum to 100 (got {total:.2f})"))
    return errors


@router.post("/validate", response_model=ValidationResponse)
def validate_plan(plan: PlanRequest) -> ValidationResponse:
    errors = _validate_allocation(plan.allocation)
    if plan.profile.current_age < 0:
        errors.append(FieldError(field="profile.current_age", message="Age must be non-negative"))
    if plan.profile.current_age > 120:
        errors.append(FieldError(field="profile.current_age", message="Age must be ≤ 120"))
    for i, seg in enumerate(plan.income):
        if seg.until and hasattr(seg.until, 'age') and seg.until.age <= plan.profile.current_age:
            errors.append(FieldError(
                field=f"income[{i}].until.age",
                message="Segment end age must be greater than current age"
            ))
    return ValidationResponse(errors=errors)


@router.post("/simulate", response_model=SimulationResult)
def simulate_plan(plan: PlanRequest) -> SimulationResult:
    alloc_errors = _validate_allocation(plan.allocation)
    if alloc_errors:
        raise HTTPException(status_code=422, detail=alloc_errors[0].message)

    try:
        import rust_core
    except ImportError:
        raise HTTPException(status_code=503, detail="Simulation engine not available (rust_core not built)")

    net_cash_flows = compute_net_cash_flows(
        profile=plan.profile,
        income_segments=plan.income,
        expenses=plan.expenses,
        goals=plan.goals,
        remainder_to=plan.remainder_to,
        n_years=HORIZON_YEARS,
    )

    alloc = plan.allocation
    allocation_weights = [
        alloc.equities / 100.0,
        alloc.bonds / 100.0,
        alloc.cash / 100.0,
        alloc.other / 100.0,
    ]

    raw = rust_core.simulate(
        initial_net_worth=plan.profile.current_net_worth,
        cash_flows=net_cash_flows,
        allocation=allocation_weights,
        return_assumptions=RETURN_ASSUMPTIONS,
        num_paths=NUM_PATHS,
        current_age=plan.profile.current_age,
    )

    by_age = [
        AgeQuantiles(
            age=q["age"],
            p1=q["p1"], p5=q["p5"], p10=q["p10"], p25=q["p25"], p50=q["p50"],
            p75=q["p75"], p90=q["p90"], p95=q["p95"], p99=q["p99"],
        )
        for q in raw["by_age"]
    ]
    return SimulationResult(by_age=by_age, ruin_probability=raw["ruin_probability"])
