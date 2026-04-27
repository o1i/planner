import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

VALID_PLAN = {
    "profile": {"current_age": 35, "current_net_worth": 100000},
    "income": [{"value": 80000, "until": None, "one_off": False}],
    "expenses": {
        "fixed": [{"label": "Rent", "segments": [{"value": 20000, "until": None, "one_off": False}]}],
        "variable": [], "guilt_free": [], "savings": [], "investments": []
    },
    "goals": [],
    "remainder_to": "investments",
    "allocation": {"equities": 60, "bonds": 30, "cash": 5, "other": 5},
}


class TestValidate:
    def test_valid_plan_returns_no_errors(self):
        r = client.post("/api/validate", json=VALID_PLAN)
        assert r.status_code == 200
        assert r.json()["errors"] == []

    def test_allocation_not_summing_to_100(self):
        bad = {**VALID_PLAN, "allocation": {"equities": 50, "bonds": 30, "cash": 5, "other": 5}}
        r = client.post("/api/validate", json=bad)
        assert r.status_code == 200
        errors = r.json()["errors"]
        assert any("100" in e["message"] for e in errors)

    def test_negative_age_rejected(self):
        bad = {**VALID_PLAN, "profile": {"current_age": -1, "current_net_worth": 0}}
        r = client.post("/api/validate", json=bad)
        assert r.status_code == 200
        errors = r.json()["errors"]
        assert any("age" in e["field"] for e in errors)


class TestSimulate:
    def _mock_rust_output(self):
        mock_rust = MagicMock()
        mock_rust.simulate.return_value = {
            "by_age": [
                {"age": 35 + i, "p1": 0.0, "p5": 0.0, "p10": 0.0, "p25": 0.0,
                 "p50": float(i * 1000), "p75": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}
                for i in range(51)
            ],
            "ruin_probability": 0.05,
        }
        return mock_rust

    def test_simulate_returns_result(self):
        with patch.dict("sys.modules", {"rust_core": self._mock_rust_output()}):
            r = client.post("/api/simulate", json=VALID_PLAN)
        assert r.status_code == 200
        body = r.json()
        assert "by_age" in body
        assert "ruin_probability" in body
        assert body["ruin_probability"] == pytest.approx(0.05)
        assert len(body["by_age"]) == 51

    def test_simulate_bad_allocation_returns_422(self):
        bad = {**VALID_PLAN, "allocation": {"equities": 50, "bonds": 30, "cash": 5, "other": 5}}
        r = client.post("/api/simulate", json=bad)
        assert r.status_code == 422
