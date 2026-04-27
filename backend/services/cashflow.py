from __future__ import annotations
from datetime import date
from models.plan import Segment, LineItem, Expenses, Profile

HORIZON_YEARS = 50


def _until_to_index(until, current_age: int) -> int:
    if hasattr(until, 'age'):
        return until.age - current_age
    current_year = date.today().year
    return until.year - current_year


def expand_segments(segments: list[Segment], current_age: int, n_years: int) -> list[float]:
    """
    Expand ordered segments into a per-year list of length n_years (index 0 = year 1).
    Segments chain: segment[i] starts where segment[i-1] ends. One-offs apply for one year only.
    """
    result = [0.0] * n_years
    cursor = 0
    for seg in segments:
        if cursor >= n_years:
            break
        if seg.one_off:
            if cursor < n_years:
                result[cursor] += seg.value
            cursor += 1
        else:
            end = n_years if seg.until is None else min(_until_to_index(seg.until, current_age), n_years)
            for i in range(cursor, end):
                result[i] = seg.value
            cursor = end
    return result


def expand_line_items(items: list[LineItem], current_age: int, n_years: int) -> list[float]:
    total = [0.0] * n_years
    for item in items:
        series = expand_segments(item.segments, current_age, n_years)
        for i in range(n_years):
            total[i] += series[i]
    return total


def compute_net_cash_flows(
    profile: Profile,
    income_segments: list[Segment],
    expenses: Expenses,
    goals: list[LineItem],
    remainder_to: str,
    n_years: int = HORIZON_YEARS,
) -> list[float]:
    """
    Returns net CHF cash flow per year for the simulation.
    Positive = portfolio inflow, negative = outflow.

    investments category entries are NOT subtracted — they represent money already
    going to the portfolio. Remainder allocation to a spending/savings category
    increases that outflow, reducing net cash flow.
    """
    age = profile.current_age

    income     = expand_segments(income_segments, age, n_years)
    fixed      = expand_line_items(expenses.fixed,       age, n_years)
    variable   = expand_line_items(expenses.variable,    age, n_years)
    guilt_free = expand_line_items(expenses.guilt_free,  age, n_years)
    savings    = expand_line_items(expenses.savings,     age, n_years)
    investments = expand_line_items(expenses.investments, age, n_years)
    goals_flow = expand_line_items(goals,                age, n_years)

    result = []
    for i in range(n_years):
        # Outflows that leave the portfolio permanently
        outflow = fixed[i] + variable[i] + guilt_free[i] + savings[i] + goals_flow[i]
        # Remainder = income minus all explicit budget items
        remainder = income[i] - outflow - investments[i]
        # If user directs remainder to a non-investment category, it leaves the portfolio
        if remainder_to in ('fixed', 'variable', 'guilt_free', 'savings'):
            outflow += remainder
        # If remainder_to == 'investments': remainder stays in portfolio (no change to outflow)
        result.append(income[i] - outflow)
    return result
