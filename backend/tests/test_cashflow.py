import pytest
from models.plan import Segment, LineItem, Expenses, Profile, UntilAge, UntilYear
from services.cashflow import expand_segments, expand_line_items, compute_net_cash_flows


def seg(value, *, age=None, year=None, one_off=False):
    until = UntilAge(age=age) if age else (UntilYear(year=year) if year else None)
    return Segment(value=value, until=until, one_off=one_off)

def item(label, *segments):
    return LineItem(label=label, segments=list(segments))

def profile(age=30, net_worth=0.0):
    return Profile(current_age=age, current_net_worth=net_worth)


class TestExpandSegments:
    def test_single_indefinite_segment(self):
        result = expand_segments([seg(1000)], current_age=30, n_years=3)
        assert result == [1000.0, 1000.0, 1000.0]

    def test_segment_until_age(self):
        # 1000/year until age 32 (2 years from age 30)
        result = expand_segments([seg(1000, age=32)], current_age=30, n_years=5)
        assert result == [1000.0, 1000.0, 0.0, 0.0, 0.0]

    def test_step_change(self):
        # 1000 until age 32, then 2000
        result = expand_segments([seg(1000, age=32), seg(2000)], current_age=30, n_years=4)
        assert result == [1000.0, 1000.0, 2000.0, 2000.0]

    def test_one_off_applies_once(self):
        result = expand_segments([seg(5000, one_off=True)], current_age=30, n_years=3)
        assert result == [5000.0, 0.0, 0.0]

    def test_until_year(self, monkeypatch):
        import services.cashflow as cf
        import datetime
        monkeypatch.setattr(cf, 'date', type('d', (), {'today': staticmethod(lambda: datetime.date(2026, 1, 1))})())
        result = expand_segments([seg(500, year=2028)], current_age=30, n_years=4)
        assert result == [500.0, 500.0, 0.0, 0.0]


class TestComputeNetCashFlows:
    def test_income_minus_spending(self):
        # income 100, fixed 60 → net 40
        p = profile(30)
        expenses = Expenses(fixed=[item("rent", seg(60))])
        result = compute_net_cash_flows(p, [seg(100)], expenses, [], 'investments', n_years=3)
        assert result == [40.0, 40.0, 40.0]

    def test_remainder_to_savings_reduces_net(self):
        # income 100, fixed 60, investments 0 → remainder 40 goes to savings (not portfolio)
        p = profile(30)
        expenses = Expenses(fixed=[item("rent", seg(60))])
        result = compute_net_cash_flows(p, [seg(100)], expenses, [], 'savings', n_years=2)
        # remainder 40 added to savings outflow → net = 100 - 60 - 40 = 0
        assert result == [0.0, 0.0]

    def test_remainder_to_investments_unchanged(self):
        # income 100, fixed 60, remainder 40 → investments → net stays 40
        p = profile(30)
        expenses = Expenses(fixed=[item("rent", seg(60))])
        result = compute_net_cash_flows(p, [seg(100)], expenses, [], 'investments', n_years=2)
        assert result == [40.0, 40.0]

    def test_explicit_investments_not_subtracted(self):
        # income 100, fixed 60, investments_entry 10 → remainder 30 → investments
        # net = 100 - 60 = 40 (investments entry not subtracted)
        p = profile(30)
        expenses = Expenses(
            fixed=[item("rent", seg(60))],
            investments=[item("etf", seg(10))]
        )
        result = compute_net_cash_flows(p, [seg(100)], expenses, [], 'investments', n_years=2)
        assert result == [40.0, 40.0]

    def test_goal_one_off_reduces_net_at_correct_year(self):
        # income 100, no expenses, one-off goal of 30 at year index 0
        p = profile(30)
        goals = [item("car", seg(30, one_off=True), seg(0))]
        result = compute_net_cash_flows(p, [seg(100)], Expenses(), goals, 'investments', n_years=3)
        assert result[0] == pytest.approx(70.0)
        assert result[1] == pytest.approx(100.0)
        assert result[2] == pytest.approx(100.0)
