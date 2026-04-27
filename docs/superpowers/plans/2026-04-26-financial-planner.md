# Financial Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a guided 4-step financial planning web app (profile → goals → budget/income → allocation → Monte Carlo simulation) with SvelteKit frontend, FastAPI backend, and Rust PyO3 simulation engine.

**Architecture:** All wizard state lives in a SvelteKit reactive store (session-only, v1). FastAPI is a stateless REST API: it expands segments into cash flows and calls the Rust PyO3 extension for Monte Carlo simulation. Docker Compose runs both services locally.

**Tech Stack:** SvelteKit 5 + TypeScript + ECharts, FastAPI + Python 3.12 + pytest, Rust + PyO3 0.22 + rand 0.8 + rand_distr 0.4 + approx 0.5, maturin (Rust→Python wheel), Docker Compose.

---

## File Map

```
planner/
├── Dockerfile
├── docker-compose.yml
├── frontend/
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── .env.example
│   └── src/
│       ├── app.html
│       ├── app.d.ts
│       ├── lib/
│       │   ├── types.ts                     shared TypeScript interfaces
│       │   ├── store.svelte.ts              Svelte 5 rune-based plan store
│       │   ├── cashflow.ts                  client-side segment→series expansion (for chart)
│       │   ├── api.ts                       fetch wrappers for /api/simulate, /api/validate
│       │   └── components/
│       │       ├── WizardNav.svelte         top progress bar
│       │       ├── SegmentEditor.svelte     reusable segment list editor
│       │       ├── LineItemEditor.svelte    reusable labelled line-item editor
│       │       ├── CashFlowChart.svelte     ECharts stacked area chart
│       │       ├── FanChart.svelte          ECharts net-worth fan chart
│       │       └── RuinGauge.svelte         ruin probability display
│       └── routes/
│           ├── +layout.svelte
│           ├── +page.svelte                 profile (age + net worth)
│           ├── step1/+page.svelte           goals
│           ├── step2/+page.svelte           budget & income
│           ├── step3/+page.svelte           asset allocation
│           └── step4/+page.svelte           simulation results
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── core/__init__.py
│   ├── core/config.py
│   ├── models/__init__.py
│   ├── models/plan.py                       Pydantic request/response models
│   ├── routers/__init__.py
│   ├── routers/plan.py                      /api/simulate, /api/validate
│   ├── services/__init__.py
│   ├── services/cashflow.py                 segment expansion + net cash flow logic
│   └── tests/
│       ├── conftest.py
│       ├── test_cashflow.py
│       └── test_routes.py
└── rust/
    ├── Cargo.toml
    ├── pyproject.toml
    └── src/
        ├── lib.rs                           PyO3 bindings
        └── simulation.rs                    Monte Carlo engine (pure Rust)
```

---

### Task 1: Project scaffold

**Files:** `backend/` tree, `.gitignore` additions, `backend/main.py`, `backend/requirements.txt`, `backend/core/config.py`, `backend/tests/conftest.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p backend/{core,models,routers,services,tests}
mkdir -p rust/src
mkdir -p frontend/src/{lib/components,routes/{step1,step2,step3,step4}}
mkdir -p docs/superpowers/{specs,plans}
```

- [ ] **Step 2: Append to `.gitignore`**

```
# Frontend
frontend/node_modules/
frontend/.svelte-kit/
frontend/build/

# Rust
rust/target/
*.whl

# Env files
backend/.env
frontend/.env

# Superpowers
.superpowers/
```

- [ ] **Step 3: Create `backend/requirements.txt`**

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic-settings>=2.0.0
pytest>=8.0.0
httpx>=0.27.0
```

- [ ] **Step 4: Create `backend/.env.example`**

```
CORS_ORIGINS=["http://localhost:5173"]
```

- [ ] **Step 5: Create `backend/core/__init__.py`** (empty file)

- [ ] **Step 6: Create `backend/core/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:5173"]
    model_config = {"env_file": ".env"}

settings = Settings()
```

- [ ] **Step 7: Create empty `__init__.py` files**

```bash
touch backend/models/__init__.py backend/routers/__init__.py backend/services/__init__.py
```

- [ ] **Step 8: Create `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}
```

- [ ] **Step 9: Create `backend/tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from main import app

@pytest.fixture
def client():
    return TestClient(app)
```

- [ ] **Step 10: Verify backend starts**

```bash
cd backend && pip install -r requirements.txt && python -c "from main import app; print('ok')"
```

Expected: `ok`

- [ ] **Step 11: Commit**

```bash
git add .
git commit -m "feat: scaffold backend project structure"
```

---

### Task 2: Dockerfile + docker-compose

**Files:** `Dockerfile`, `docker-compose.yml`, `frontend/.env.example`

- [ ] **Step 1: Create `Dockerfile`**

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl build-essential && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:$PATH"

RUN pip install maturin

WORKDIR /rust
COPY rust/ .
RUN maturin build --release && pip install target/wheels/*.whl

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 2: Create `docker-compose.yml`**

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - CORS_ORIGINS=["http://localhost:5173"]
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    restart: unless-stopped

  frontend:
    image: node:22-alpine
    working_dir: /app
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
    command: sh -c "npm install && npm run dev -- --host 0.0.0.0"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
```

- [ ] **Step 3: Create `frontend/.env.example`**

```
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml frontend/.env.example
git commit -m "feat: add Dockerfile and docker-compose for local dev"
```

---

### Task 3: Rust crate setup

**Files:** `rust/Cargo.toml`, `rust/pyproject.toml`, `rust/src/lib.rs`, `rust/src/simulation.rs`

- [ ] **Step 1: Write `rust/Cargo.toml`**

```toml
[package]
name = "rust_core"
version = "0.1.0"
edition = "2021"

[lib]
name = "rust_core"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.22", features = ["extension-module"] }
rand = "0.8"
rand_distr = "0.4"

[dev-dependencies]
approx = "0.5"
```

- [ ] **Step 2: Write `rust/pyproject.toml`**

```toml
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "rust_core"
version = "0.1.0"
requires-python = ">=3.10"

[tool.maturin]
features = ["pyo3/extension-module"]
```

- [ ] **Step 3: Create `rust/src/simulation.rs`** (stub)

```rust
// Monte Carlo simulation engine — pure Rust, no PyO3 dependency
```

- [ ] **Step 4: Write `rust/src/lib.rs`** (stub)

```rust
use pyo3::prelude::*;

mod simulation;

#[pymodule]
fn rust_core(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    Ok(())
}
```

- [ ] **Step 5: Verify compilation**

```bash
cd rust && cargo check
```

Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add rust/
git commit -m "feat: set up rust crate with pyo3 rand rand_distr"
```

---

### Task 4: Rust simulation engine

**Files:** `rust/src/simulation.rs`

**Cash flow model:** `net_cash_flow[t] = income[t] - fixed[t] - variable[t] - guilt_free[t] - savings[t] - goals[t]`. The `investments` category is money staying in the portfolio so it is NOT subtracted. Remainder allocation to a spending/savings category reduces net_cash_flow; allocation to investments leaves it unchanged. Python computes this before calling Rust. Rust receives only the final net cash flow vector.

- [ ] **Step 1: Write `rust/src/simulation.rs`**

```rust
use rand::SeedableRng;
use rand::rngs::StdRng;
use rand_distr::{Normal, Distribution};

pub struct ReturnAssumption {
    /// Annualised log drift (e.g. 0.07 ≈ 7%). For 100% doubling: use ln(2) ≈ 0.693.
    pub mean: f64,
    /// Annualised volatility. Set to 0.0 for deterministic tests.
    pub std_dev: f64,
}

pub struct SimulationInput {
    pub initial_net_worth: f64,
    /// Net CHF added to portfolio per year. Index 0 = first year from now.
    pub cash_flows: Vec<f64>,
    /// [equities, bonds, cash, other] weights summing to 1.0.
    pub allocation: [f64; 4],
    pub return_assumptions: [ReturnAssumption; 4],
    pub num_paths: usize,
    pub current_age: u32,
    pub seed: Option<u64>,
}

pub struct AgeQuantiles {
    pub age: u32,
    pub p1: f64, pub p5: f64, pub p10: f64, pub p25: f64, pub p50: f64,
    pub p75: f64, pub p90: f64, pub p95: f64, pub p99: f64,
}

pub struct SimulationOutput {
    pub by_age: Vec<AgeQuantiles>,
    pub ruin_probability: f64,
}

pub fn run_simulation(input: &SimulationInput) -> SimulationOutput {
    let n_years = input.cash_flows.len();
    let n_paths = input.num_paths;

    // Effective portfolio log-drift and volatility (uncorrelated asset classes).
    let mu_eff: f64 = input.allocation.iter().zip(input.return_assumptions.iter())
        .map(|(w, r)| w * r.mean).sum();
    let var_eff: f64 = input.allocation.iter().zip(input.return_assumptions.iter())
        .map(|(w, r)| w * w * r.std_dev * r.std_dev).sum();
    let sigma_eff = var_eff.sqrt();

    let mut rng: StdRng = match input.seed {
        Some(s) => StdRng::seed_from_u64(s),
        None => StdRng::from_entropy(),
    };

    // net_worths[year][path]
    let mut net_worths: Vec<Vec<f64>> = vec![vec![0.0; n_paths]; n_years + 1];
    for p in 0..n_paths { net_worths[0][p] = input.initial_net_worth; }
    let mut ruin_flags = vec![false; n_paths];

    if sigma_eff < 1e-12 {
        // Deterministic: all paths identical, no random sampling needed.
        let annual_factor = mu_eff.exp();
        for path in 0..n_paths {
            for year in 0..n_years {
                let next = net_worths[year][path] * annual_factor + input.cash_flows[year];
                net_worths[year + 1][path] = next;
                if next <= 0.0 { ruin_flags[path] = true; }
            }
        }
    } else {
        // GBM: annual log return ~ Normal(mu - 0.5σ², σ)
        let log_drift = mu_eff - 0.5 * sigma_eff * sigma_eff;
        let normal = Normal::new(log_drift, sigma_eff).unwrap();
        for path in 0..n_paths {
            for year in 0..n_years {
                let log_r = normal.sample(&mut rng);
                let next = net_worths[year][path] * log_r.exp() + input.cash_flows[year];
                net_worths[year + 1][path] = next;
                if next <= 0.0 { ruin_flags[path] = true; }
            }
        }
    }

    let ruin_count = ruin_flags.iter().filter(|&&f| f).count();

    let quantile = |year: usize, pct: f64| -> f64 {
        let mut vals: Vec<f64> = net_worths[year].clone();
        vals.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let idx = ((pct * (n_paths - 1) as f64).round() as usize).min(n_paths - 1);
        vals[idx]
    };

    let by_age = (0..=n_years).map(|year| AgeQuantiles {
        age: input.current_age + year as u32,
        p1:  quantile(year, 0.01), p5:  quantile(year, 0.05),
        p10: quantile(year, 0.10), p25: quantile(year, 0.25),
        p50: quantile(year, 0.50), p75: quantile(year, 0.75),
        p90: quantile(year, 0.90), p95: quantile(year, 0.95),
        p99: quantile(year, 0.99),
    }).collect();

    SimulationOutput {
        by_age,
        ruin_probability: ruin_count as f64 / n_paths as f64,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;

    fn equity_only(mean: f64, std_dev: f64) -> ([f64; 4], [ReturnAssumption; 4]) {
        (
            [1.0, 0.0, 0.0, 0.0],
            [
                ReturnAssumption { mean, std_dev },
                ReturnAssumption { mean: 0.0, std_dev: 0.0 },
                ReturnAssumption { mean: 0.0, std_dev: 0.0 },
                ReturnAssumption { mean: 0.0, std_dev: 0.0 },
            ],
        )
    }

    #[test]
    fn zero_return_income_surplus_grows_linearly() {
        // 0% return, +1000 CHF/year net → net worth grows by exactly 1000/year
        let (alloc, ra) = equity_only(0.0, 0.0);
        let out = run_simulation(&SimulationInput {
            initial_net_worth: 0.0,
            cash_flows: vec![1000.0; 10],
            allocation: alloc, return_assumptions: ra,
            num_paths: 5, current_age: 30, seed: Some(42),
        });
        for (i, q) in out.by_age.iter().enumerate() {
            let expected = i as f64 * 1000.0;
            assert_abs_diff_eq!(q.p1,  expected, epsilon = 1e-6);
            assert_abs_diff_eq!(q.p50, expected, epsilon = 1e-6);
            assert_abs_diff_eq!(q.p99, expected, epsilon = 1e-6);
        }
        assert_abs_diff_eq!(out.ruin_probability, 0.0, epsilon = 1e-10);
    }

    #[test]
    fn zero_return_deficit_ruin_at_correct_age() {
        // 0% return, -1000 CHF/year, start 5000 → ruin at year 5 (age 35)
        let (alloc, ra) = equity_only(0.0, 0.0);
        let out = run_simulation(&SimulationInput {
            initial_net_worth: 5000.0,
            cash_flows: vec![-1000.0; 10],
            allocation: alloc, return_assumptions: ra,
            num_paths: 5, current_age: 30, seed: Some(42),
        });
        assert_abs_diff_eq!(out.by_age[5].p50, 0.0,    epsilon = 1e-6);
        assert!(out.by_age[6].p50 < 0.0);
        assert_abs_diff_eq!(out.ruin_probability, 1.0, epsilon = 1e-10);
    }

    #[test]
    fn hundred_percent_return_doubles_each_year() {
        // mu = ln(2), sigma = 0 → net worth doubles each year
        let (alloc, ra) = equity_only(std::f64::consts::LN_2, 0.0);
        let out = run_simulation(&SimulationInput {
            initial_net_worth: 1000.0,
            cash_flows: vec![0.0; 4],
            allocation: alloc, return_assumptions: ra,
            num_paths: 3, current_age: 40, seed: Some(0),
        });
        assert_abs_diff_eq!(out.by_age[0].p50, 1000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.by_age[1].p50, 2000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.by_age[2].p50, 4000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.by_age[3].p50, 8000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.ruin_probability, 0.0, epsilon = 1e-10);
    }

    #[test]
    fn one_off_expense_drops_net_worth_at_correct_year() {
        // 0% return, start 10000, one-off -3000 at year index 2 → worth drops at year 3
        let (alloc, ra) = equity_only(0.0, 0.0);
        let mut cash_flows = vec![0.0; 5];
        cash_flows[2] = -3000.0;
        let out = run_simulation(&SimulationInput {
            initial_net_worth: 10000.0,
            cash_flows,
            allocation: alloc, return_assumptions: ra,
            num_paths: 3, current_age: 50, seed: Some(0),
        });
        assert_abs_diff_eq!(out.by_age[2].p50, 10000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.by_age[3].p50,  7000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.by_age[4].p50,  7000.0, epsilon = 1e-6);
    }

    #[test]
    fn age_offset_applied_correctly() {
        let (alloc, ra) = equity_only(0.0, 0.0);
        let out = run_simulation(&SimulationInput {
            initial_net_worth: 0.0,
            cash_flows: vec![0.0; 3],
            allocation: alloc, return_assumptions: ra,
            num_paths: 2, current_age: 35, seed: Some(0),
        });
        assert_eq!(out.by_age[0].age, 35);
        assert_eq!(out.by_age[1].age, 36);
        assert_eq!(out.by_age[3].age, 38);
    }
}
```

- [ ] **Step 2: Run tests**

```bash
cd rust && cargo test
```

Expected: 5 tests pass

- [ ] **Step 3: Commit**

```bash
git add rust/src/simulation.rs
git commit -m "feat: GBM Monte Carlo engine with deterministic tests"
```

---

### Task 5: Rust PyO3 bindings

**Files:** `rust/src/lib.rs`

- [ ] **Step 1: Write `rust/src/lib.rs`**

```rust
use pyo3::prelude::*;
use pyo3::types::PyDict;

mod simulation;
use simulation::{ReturnAssumption, SimulationInput, run_simulation};

#[pyfunction]
#[pyo3(signature = (initial_net_worth, cash_flows, allocation, return_assumptions, num_paths, current_age, seed=None))]
fn simulate(
    py: Python<'_>,
    initial_net_worth: f64,
    cash_flows: Vec<f64>,
    allocation: [f64; 4],
    return_assumptions: Vec<(f64, f64)>,
    num_paths: usize,
    current_age: u32,
    seed: Option<u64>,
) -> PyResult<PyObject> {
    if return_assumptions.len() != 4 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "return_assumptions must have exactly 4 elements"
        ));
    }
    let ra: [ReturnAssumption; 4] = std::array::from_fn(|i| ReturnAssumption {
        mean: return_assumptions[i].0,
        std_dev: return_assumptions[i].1,
    });
    let output = run_simulation(&SimulationInput {
        initial_net_worth, cash_flows,
        allocation, return_assumptions: ra,
        num_paths, current_age, seed,
    });

    let result = PyDict::new_bound(py);
    let by_age_list: Vec<PyObject> = output.by_age.iter().map(|q| {
        let d = PyDict::new_bound(py);
        d.set_item("age", q.age).unwrap();
        d.set_item("p1",  q.p1).unwrap();  d.set_item("p5",  q.p5).unwrap();
        d.set_item("p10", q.p10).unwrap(); d.set_item("p25", q.p25).unwrap();
        d.set_item("p50", q.p50).unwrap(); d.set_item("p75", q.p75).unwrap();
        d.set_item("p90", q.p90).unwrap(); d.set_item("p95", q.p95).unwrap();
        d.set_item("p99", q.p99).unwrap();
        d.into()
    }).collect();
    result.set_item("by_age", by_age_list)?;
    result.set_item("ruin_probability", output.ruin_probability)?;
    Ok(result.into())
}

#[pymodule]
fn rust_core(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(simulate, m)?)?;
    Ok(())
}
```

- [ ] **Step 2: Verify compilation**

```bash
cd rust && cargo check
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add rust/src/lib.rs
git commit -m "feat: add PyO3 bindings exposing simulate()"
```

---

### Task 6: Python Pydantic models

**Files:** `backend/models/plan.py`

- [ ] **Step 1: Write `backend/models/plan.py`**

```python
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
```

- [ ] **Step 2: Verify import**

```bash
cd backend && python -c "from models.plan import PlanRequest, SimulationResult; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add backend/models/plan.py
git commit -m "feat: pydantic models for plan API"
```

---

### Task 7: Python cashflow service

**Files:** `backend/services/cashflow.py`

**Model:** `net_cash_flow = income - fixed - variable - guilt_free - savings - goals`. The `investments` category represents money going directly into the portfolio so it is NOT subtracted. If remainder_to is a spending/savings category, that category's total increases (reducing net cash flow). If remainder_to is `investments`, the remainder stays in the portfolio and net cash flow is unchanged.

- [ ] **Step 1: Write `backend/services/cashflow.py`**

```python
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
```

- [ ] **Step 2: Verify import**

```bash
cd backend && python -c "from services.cashflow import compute_net_cash_flows; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add backend/services/cashflow.py
git commit -m "feat: cashflow service for segment expansion and net cash flow"
```

---

### Task 8: Python cashflow service tests

**Files:** `backend/tests/test_cashflow.py`

- [ ] **Step 1: Write `backend/tests/test_cashflow.py`**

```python
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
        # Pretend current year is 2026; segment until 2028 = 2 years
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
        # income 100, no expenses, one-off goal of 30 at year index 1
        p = profile(30)
        goals = [item("car", seg(30, one_off=True), seg(0))]
        # One-off at cursor 0, then 0 indefinitely
        result = compute_net_cash_flows(p, [seg(100)], Expenses(), goals, 'investments', n_years=3)
        assert result[0] == pytest.approx(70.0)
        assert result[1] == pytest.approx(100.0)
        assert result[2] == pytest.approx(100.0)
```

- [ ] **Step 2: Run tests**

```bash
cd backend && python -m pytest tests/test_cashflow.py -v
```

Expected: all tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_cashflow.py
git commit -m "test: cashflow service unit tests"
```

---

### Task 9: Python API routes

**Files:** `backend/routers/plan.py`, update `backend/main.py`

Default return assumptions (hardcoded v1): equities (0.07, 0.15), bonds (0.03, 0.05), cash (0.005, 0.005), other (0.05, 0.10).

- [ ] **Step 1: Write `backend/routers/plan.py`**

```python
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
```

- [ ] **Step 2: Register router in `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers.plan import router as plan_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plan_router)

@app.get("/")
def root():
    return {"status": "ok"}
```

- [ ] **Step 3: Commit**

```bash
git add backend/routers/plan.py backend/main.py
git commit -m "feat: /api/validate and /api/simulate endpoints"
```

---

### Task 10: Python route tests

**Files:** `backend/tests/test_routes.py`

These tests mock `rust_core` so they run without a compiled Rust wheel.

- [ ] **Step 1: Write `backend/tests/test_routes.py`**

```python
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
```

- [ ] **Step 2: Run tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_routes.py
git commit -m "test: API route tests with mocked rust_core"
```

---

### Task 11: SvelteKit scaffold

**Files:** `frontend/package.json`, `frontend/svelte.config.js`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/src/app.html`, `frontend/src/app.d.ts`

- [ ] **Step 1: Write `frontend/package.json`**

```json
{
  "name": "financial-planner",
  "version": "0.0.1",
  "private": true,
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
    "test": "vitest run"
  },
  "devDependencies": {
    "@sveltejs/adapter-cloudflare": "^4.0.0",
    "@sveltejs/kit": "^2.0.0",
    "@sveltejs/vite-plugin-svelte": "^4.0.0",
    "svelte": "^5.0.0",
    "svelte-check": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^6.0.0",
    "vitest": "^2.0.0",
    "@testing-library/svelte": "^5.0.0",
    "jsdom": "^25.0.0"
  },
  "dependencies": {
    "echarts": "^5.5.0"
  }
}
```

- [ ] **Step 2: Write `frontend/svelte.config.js`**

```js
import adapter from '@sveltejs/adapter-cloudflare';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  kit: { adapter: adapter() },
};
```

- [ ] **Step 3: Write `frontend/vite.config.ts`**

```typescript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    environment: 'jsdom',
    include: ['src/**/*.{test,spec}.{js,ts}'],
  },
});
```

- [ ] **Step 4: Write `frontend/tsconfig.json`**

```json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "sourceMap": true,
    "strict": true
  }
}
```

- [ ] **Step 5: Write `frontend/src/app.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

- [ ] **Step 6: Write `frontend/src/app.d.ts`**

```typescript
declare global {
  namespace App {}
}
export {};
```

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: SvelteKit scaffold with vitest and echarts"
```

---

### Task 12: Frontend types and store

**Files:** `frontend/src/lib/types.ts`, `frontend/src/lib/store.svelte.ts`

- [ ] **Step 1: Write `frontend/src/lib/types.ts`**

```typescript
export interface UntilAge  { age: number }
export interface UntilYear { year: number }

export interface Segment {
  value: number
  until: UntilAge | UntilYear | null
  oneOff: boolean
}

export interface LineItem {
  label: string
  segments: Segment[]
}

export interface Expenses {
  fixed:       LineItem[]
  variable:    LineItem[]
  guiltFree:   LineItem[]
  savings:     LineItem[]
  investments: LineItem[]
}

export interface Allocation {
  equities: number
  bonds: number
  cash: number
  other: number
}

export interface AgeQuantiles {
  age: number
  p1: number; p5: number; p10: number; p25: number; p50: number
  p75: number; p90: number; p95: number; p99: number
}

export interface SimulationResult {
  byAge: AgeQuantiles[]
  ruinProbability: number
}

export type RemainderCategory = 'fixed' | 'variable' | 'guiltFree' | 'savings' | 'investments'

export interface PlanState {
  profile: { currentAge: number; currentNetWorth: number }
  goals: LineItem[]
  income: Segment[]
  expenses: Expenses
  remainderTo: RemainderCategory
  allocation: Allocation
  simulationResult: SimulationResult | null
  isDirty: boolean
}
```

- [ ] **Step 2: Write `frontend/src/lib/store.svelte.ts`**

```typescript
import type { PlanState, RemainderCategory } from './types';

const initial: PlanState = {
  profile: { currentAge: 0, currentNetWorth: 0 },
  goals: [],
  income: [],
  expenses: { fixed: [], variable: [], guiltFree: [], savings: [], investments: [] },
  remainderTo: 'investments',
  allocation: { equities: 60, bonds: 30, cash: 5, other: 5 },
  simulationResult: null,
  isDirty: false,
};

export const plan = $state<PlanState>(structuredClone(initial));

export function markDirty() {
  if (plan.simulationResult !== null) {
    plan.isDirty = true;
  }
}

export function clearSimulation() {
  plan.simulationResult = null;
  plan.isDirty = false;
}

export function resetPlan() {
  Object.assign(plan, structuredClone(initial));
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/store.svelte.ts
git commit -m "feat: TypeScript types and Svelte 5 rune store"
```

---

### Task 13: Frontend cashflow helpers and API client

**Files:** `frontend/src/lib/cashflow.ts`, `frontend/src/lib/api.ts`

- [ ] **Step 1: Write `frontend/src/lib/cashflow.ts`**

This is the client-side version of the Python segment expansion — used for the live Step 2 chart without a backend round-trip.

```typescript
import type { Segment, LineItem, Expenses } from './types';

const HORIZON = 50;

function untilToIndex(until: { age?: number; year?: number }, currentAge: number): number {
  if ('age' in until && until.age !== undefined) return until.age - currentAge;
  const currentYear = new Date().getFullYear();
  return (until.year ?? currentYear) - currentYear;
}

export function expandSegments(segments: Segment[], currentAge: number, nYears = HORIZON): number[] {
  const result = new Array<number>(nYears).fill(0);
  let cursor = 0;
  for (const seg of segments) {
    if (cursor >= nYears) break;
    if (seg.oneOff) {
      if (cursor < nYears) result[cursor] += seg.value;
      cursor++;
    } else {
      const end = seg.until === null ? nYears : Math.min(untilToIndex(seg.until, currentAge), nYears);
      for (let i = cursor; i < end; i++) result[i] = seg.value;
      cursor = end;
    }
  }
  return result;
}

export function expandLineItems(items: LineItem[], currentAge: number, nYears = HORIZON): number[] {
  const total = new Array<number>(nYears).fill(0);
  for (const item of items) {
    const series = expandSegments(item.segments, currentAge, nYears);
    for (let i = 0; i < nYears; i++) total[i] += series[i];
  }
  return total;
}

export interface CashFlowSeries {
  ages: number[]
  income: number[]
  fixed: number[]
  variable: number[]
  guiltFree: number[]
  savings: number[]
  investments: number[]
  surplus: number[]   // income - sum(all categories) for delta band
}

export function buildCashFlowSeries(
  currentAge: number,
  incomeSeg: Segment[],
  expenses: Expenses,
  nYears = HORIZON,
): CashFlowSeries {
  const ages     = Array.from({ length: nYears }, (_, i) => currentAge + i);
  const income   = expandSegments(incomeSeg, currentAge, nYears);
  const fixed    = expandLineItems(expenses.fixed,       currentAge, nYears);
  const variable = expandLineItems(expenses.variable,    currentAge, nYears);
  const guiltFree = expandLineItems(expenses.guiltFree,  currentAge, nYears);
  const savings  = expandLineItems(expenses.savings,     currentAge, nYears);
  const investments = expandLineItems(expenses.investments, currentAge, nYears);
  const surplus  = income.map((v, i) => v - fixed[i] - variable[i] - guiltFree[i] - savings[i] - investments[i]);
  return { ages, income, fixed, variable, guiltFree, savings, investments, surplus };
}
```

- [ ] **Step 2: Write `frontend/src/lib/api.ts`**

```typescript
import type { PlanState, SimulationResult, AgeQuantiles } from './types';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

function toSnake(state: PlanState) {
  // Convert camelCase store shape to snake_case for the Python API
  return {
    profile: {
      current_age: state.profile.currentAge,
      current_net_worth: state.profile.currentNetWorth,
    },
    goals: state.goals.map(item => ({
      label: item.label,
      segments: item.segments.map(s => ({
        value: s.value,
        until: s.until === null ? null
          : 'age' in s.until ? { age: s.until.age }
          : { year: s.until.year },
        one_off: s.oneOff,
      })),
    })),
    income: state.income.map(s => ({
      value: s.value,
      until: s.until === null ? null
        : 'age' in s.until ? { age: s.until.age }
        : { year: s.until.year },
      one_off: s.oneOff,
    })),
    expenses: {
      fixed:       toLineItemList(state.expenses.fixed),
      variable:    toLineItemList(state.expenses.variable),
      guilt_free:  toLineItemList(state.expenses.guiltFree),
      savings:     toLineItemList(state.expenses.savings),
      investments: toLineItemList(state.expenses.investments),
    },
    remainder_to: toSnakeCategory(state.remainderTo),
    allocation: {
      equities: state.allocation.equities,
      bonds:    state.allocation.bonds,
      cash:     state.allocation.cash,
      other:    state.allocation.other,
    },
  };
}

function toLineItemList(items: typeof [] | any[]) {
  return items.map((item: any) => ({
    label: item.label,
    segments: item.segments.map((s: any) => ({
      value: s.value,
      until: s.until === null ? null
        : 'age' in s.until ? { age: s.until.age }
        : { year: s.until.year },
      one_off: s.oneOff,
    })),
  }));
}

function toSnakeCategory(c: string): string {
  return c === 'guiltFree' ? 'guilt_free' : c;
}

function fromSnakeResult(raw: any): SimulationResult {
  return {
    byAge: raw.by_age.map((q: any): AgeQuantiles => ({
      age: q.age, p1: q.p1, p5: q.p5, p10: q.p10, p25: q.p25, p50: q.p50,
      p75: q.p75, p90: q.p90, p95: q.p95, p99: q.p99,
    })),
    ruinProbability: raw.ruin_probability,
  };
}

export async function simulate(state: PlanState): Promise<SimulationResult> {
  const res = await fetch(`${BASE}/api/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(toSnake(state)),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Simulation failed (${res.status}): ${err}`);
  }
  return fromSnakeResult(await res.json());
}

export async function validate(state: PlanState): Promise<{ field: string; message: string }[]> {
  const res = await fetch(`${BASE}/api/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(toSnake(state)),
  });
  if (!res.ok) throw new Error(`Validation request failed (${res.status})`);
  return (await res.json()).errors;
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/cashflow.ts frontend/src/lib/api.ts
git commit -m "feat: cashflow helpers and API client"
```

---

### Task 14: WizardNav component and layout

**Files:** `frontend/src/lib/components/WizardNav.svelte`, `frontend/src/routes/+layout.svelte`

- [ ] **Step 1: Write `frontend/src/lib/components/WizardNav.svelte`**

```svelte
<script lang="ts">
  let { currentStep }: { currentStep: 1 | 2 | 3 | 4 } = $props();
  const steps = ['Profile', 'Goals', 'Budget & Income', 'Allocation', 'Simulation'];
  // Step 0 = profile (not numbered), steps 1-4 = wizard
</script>

<nav class="wizard-nav">
  {#each [1, 2, 3, 4] as n}
    <div class="step" class:active={currentStep === n} class:done={currentStep > n}>
      <span class="circle">{n}</span>
      <span class="label">{steps[n]}</span>
    </div>
    {#if n < 4}<div class="connector" class:filled={currentStep > n}></div>{/if}
  {/each}
</nav>

<style>
  .wizard-nav { display: flex; align-items: center; padding: 1.5rem 2rem; gap: 0; }
  .step { display: flex; align-items: center; gap: 0.5rem; }
  .circle {
    width: 2rem; height: 2rem; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 600; font-size: 0.85rem;
    background: #e5e7eb; color: #6b7280;
  }
  .step.active .circle { background: #2563eb; color: white; }
  .step.done .circle { background: #16a34a; color: white; }
  .label { font-size: 0.875rem; color: #374151; }
  .step.active .label { color: #2563eb; font-weight: 600; }
  .connector { flex: 1; height: 2px; background: #e5e7eb; min-width: 2rem; margin: 0 0.5rem; }
  .connector.filled { background: #16a34a; }
</style>
```

- [ ] **Step 2: Write `frontend/src/routes/+layout.svelte`**

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import WizardNav from '$lib/components/WizardNav.svelte';

  const stepMap: Record<string, 1 | 2 | 3 | 4> = {
    '/step1': 1, '/step2': 2, '/step3': 3, '/step4': 4,
  };
  let currentStep = $derived(stepMap[$page.url.pathname] ?? 0 as any);
  let showNav = $derived(currentStep >= 1);
</script>

<div class="app">
  {#if showNav}
    <WizardNav {currentStep} />
  {/if}
  <main>
    <slot />
  </main>
</div>

<style>
  .app { min-height: 100vh; font-family: system-ui, sans-serif; }
  main { max-width: 860px; margin: 0 auto; padding: 2rem; }
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/WizardNav.svelte frontend/src/routes/+layout.svelte
git commit -m "feat: WizardNav component and layout"
```

---

### Task 15: Profile page

**Files:** `frontend/src/routes/+page.svelte`

- [ ] **Step 1: Write `frontend/src/routes/+page.svelte`**

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  import { plan } from '$lib/store.svelte';

  let ageStr = $state(String(plan.profile.currentAge || ''));
  let worthStr = $state(String(plan.profile.currentNetWorth || ''));
  let errors = $state<{ age?: string; worth?: string }>({});

  function validate() {
    const e: typeof errors = {};
    const age = parseInt(ageStr);
    const worth = parseFloat(worthStr);
    if (!ageStr || isNaN(age) || age < 1 || age > 120) e.age = 'Enter a valid age (1–120)';
    if (!worthStr || isNaN(worth)) e.worth = 'Enter your current net worth in CHF';
    return e;
  }

  function next() {
    errors = validate();
    if (Object.keys(errors).length) return;
    plan.profile.currentAge = parseInt(ageStr);
    plan.profile.currentNetWorth = parseFloat(worthStr);
    goto('/step1');
  }
</script>

<h1>Financial Planner</h1>
<p>Let's start with a few basics about your current situation.</p>

<div class="form">
  <label>
    Your current age
    <input type="number" bind:value={ageStr} min="1" max="120" />
    {#if errors.age}<span class="error">{errors.age}</span>{/if}
  </label>
  <label>
    Current net worth (CHF)
    <input type="number" bind:value={worthStr} step="1000" />
    {#if errors.worth}<span class="error">{errors.worth}</span>{/if}
  </label>
  <button onclick={next}>Start planning →</button>
</div>

<style>
  h1 { font-size: 2rem; margin-bottom: 0.5rem; }
  .form { display: flex; flex-direction: column; gap: 1.25rem; max-width: 360px; margin-top: 2rem; }
  label { display: flex; flex-direction: column; gap: 0.4rem; font-weight: 500; }
  input { padding: 0.6rem 0.75rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: 1rem; }
  .error { color: #dc2626; font-size: 0.8rem; }
  button { padding: 0.75rem 1.5rem; background: #2563eb; color: white; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; }
  button:hover { background: #1d4ed8; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/routes/+page.svelte
git commit -m "feat: profile page (age + net worth entry)"
```

---

### Task 16: SegmentEditor component

**Files:** `frontend/src/lib/components/SegmentEditor.svelte`

Reusable editor for a `Segment[]`. Each segment row has: value (CHF), until type (age/year/indefinite), until value, and one-off checkbox. Used for income and goals.

- [ ] **Step 1: Write `frontend/src/lib/components/SegmentEditor.svelte`**

```svelte
<script lang="ts">
  import type { Segment } from '$lib/types';

  let { segments = $bindable() }: { segments: Segment[] } = $props();

  function addSegment() {
    segments = [...segments, { value: 0, until: null, oneOff: false }];
  }

  function remove(i: number) {
    segments = segments.filter((_, idx) => idx !== i);
  }

  function setUntilType(i: number, type: 'none' | 'age' | 'year') {
    const seg = { ...segments[i] };
    seg.until = type === 'none' ? null : type === 'age' ? { age: 0 } : { year: new Date().getFullYear() + 1 };
    segments = segments.map((s, idx) => idx === i ? seg : s);
  }

  function untilType(seg: Segment): 'none' | 'age' | 'year' {
    if (!seg.until) return 'none';
    return 'age' in seg.until ? 'age' : 'year';
  }
</script>

<div class="segment-editor">
  {#each segments as seg, i}
    <div class="row">
      <input type="number" placeholder="CHF/year" bind:value={seg.value} />
      <label class="one-off">
        <input type="checkbox" bind:checked={seg.oneOff} /> One-off
      </label>
      <select value={untilType(seg)} onchange={e => setUntilType(i, (e.target as HTMLSelectElement).value as any)}>
        <option value="none">Indefinite</option>
        <option value="age">Until age</option>
        <option value="year">Until year</option>
      </select>
      {#if seg.until && 'age' in seg.until}
        <input type="number" placeholder="Age" bind:value={seg.until.age} min="0" max="120" />
      {:else if seg.until && 'year' in seg.until}
        <input type="number" placeholder="Year" bind:value={seg.until.year} />
      {/if}
      <button class="remove" onclick={() => remove(i)}>✕</button>
    </div>
  {/each}
  <button class="add" onclick={addSegment}>+ Add segment</button>
</div>

<style>
  .segment-editor { display: flex; flex-direction: column; gap: 0.5rem; }
  .row { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
  input[type=number] { width: 8rem; padding: 0.4rem 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; }
  select { padding: 0.4rem 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; }
  .one-off { display: flex; align-items: center; gap: 0.3rem; font-size: 0.85rem; }
  .remove { background: none; border: none; color: #6b7280; cursor: pointer; font-size: 1rem; }
  .add { margin-top: 0.25rem; background: none; border: 1px dashed #9ca3af; color: #6b7280; padding: 0.35rem 0.75rem; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/SegmentEditor.svelte
git commit -m "feat: SegmentEditor reusable component"
```

---

### Task 17: LineItemEditor component

**Files:** `frontend/src/lib/components/LineItemEditor.svelte`

Reusable editor for a `LineItem[]`. Each item has a label and its own `SegmentEditor`.

- [ ] **Step 1: Write `frontend/src/lib/components/LineItemEditor.svelte`**

```svelte
<script lang="ts">
  import type { LineItem } from '$lib/types';
  import SegmentEditor from './SegmentEditor.svelte';

  let { items = $bindable(), placeholder = 'e.g. Rent' }: { items: LineItem[]; placeholder?: string } = $props();

  function addItem() {
    items = [...items, { label: '', segments: [{ value: 0, until: null, oneOff: false }] }];
  }

  function remove(i: number) {
    items = items.filter((_, idx) => idx !== i);
  }
</script>

<div class="line-item-editor">
  {#each items as item, i}
    <div class="item-block">
      <div class="item-header">
        <input class="label-input" type="text" placeholder={placeholder} bind:value={item.label} />
        <button class="remove" onclick={() => remove(i)}>Remove</button>
      </div>
      <SegmentEditor bind:segments={item.segments} />
    </div>
  {/each}
  <button class="add" onclick={addItem}>+ Add item</button>
</div>

<style>
  .line-item-editor { display: flex; flex-direction: column; gap: 1rem; }
  .item-block { border: 1px solid #e5e7eb; border-radius: 6px; padding: 0.75rem; }
  .item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
  .label-input { font-weight: 600; border: none; border-bottom: 1px solid #d1d5db; padding: 0.2rem; font-size: 0.95rem; width: 14rem; }
  .remove { background: none; border: none; color: #ef4444; cursor: pointer; font-size: 0.8rem; }
  .add { background: none; border: 1px dashed #9ca3af; color: #6b7280; padding: 0.4rem 0.9rem; border-radius: 4px; cursor: pointer; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/LineItemEditor.svelte
git commit -m "feat: LineItemEditor reusable component"
```

---

### Task 18: Step 1 — Goals

**Files:** `frontend/src/routes/step1/+page.svelte`

- [ ] **Step 1: Write `frontend/src/routes/step1/+page.svelte`**

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  import { plan, markDirty } from '$lib/store.svelte';
  import LineItemEditor from '$lib/components/LineItemEditor.svelte';

  function next() { markDirty(); goto('/step2'); }
</script>

<h2>Step 1 — Financial Goals</h2>
<p>Define what you're planning for. Each goal can be a recurring annual cost or a one-off payment at a specific age or year.</p>
<p class="hint">Examples: "Retirement travel: 20 000 CHF/year from age 65" or "Home renovation: 100 000 CHF at age 50 (one-off)".</p>

<LineItemEditor bind:items={plan.goals} placeholder="e.g. Travel, Home renovation" />

<div class="nav">
  <button class="secondary" onclick={() => goto('/')}>← Back</button>
  <button onclick={next}>Budget & Income →</button>
</div>

<style>
  h2 { margin-bottom: 0.5rem; }
  .hint { color: #6b7280; font-size: 0.875rem; margin-bottom: 1.5rem; }
  .nav { display: flex; gap: 1rem; margin-top: 2rem; }
  button { padding: 0.7rem 1.4rem; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; }
  button.secondary { background: #e5e7eb; color: #374151; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/routes/step1/+page.svelte
git commit -m "feat: step 1 goals page"
```

---

### Task 19: CashFlowChart component

**Files:** `frontend/src/lib/components/CashFlowChart.svelte`

Stacked area chart showing the 5 expense categories plus an income line and a surplus/deficit band. Used on Step 2 (without investment returns) and Step 4 (with investment returns included in income).

- [ ] **Step 1: Write `frontend/src/lib/components/CashFlowChart.svelte`**

```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { CashFlowSeries } from '$lib/cashflow';

  let { series }: { series: CashFlowSeries } = $props();

  let el: HTMLDivElement;
  let chart: any;

  function buildOption(s: CashFlowSeries) {
    const fmt = (v: number) => `CHF ${v.toLocaleString('de-CH', { maximumFractionDigits: 0 })}`;
    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const age = params[0]?.axisValue;
          return `<b>Age ${age}</b><br>` + params.map(p => `${p.seriesName}: ${fmt(p.value)}`).join('<br>');
        },
      },
      legend: { bottom: 0 },
      xAxis: { type: 'category', data: s.ages, name: 'Age' },
      yAxis: { type: 'value', axisLabel: { formatter: (v: number) => `${(v/1000).toFixed(0)}k` } },
      series: [
        { name: 'Fixed',        type: 'bar', stack: 'expense', data: s.fixed,      itemStyle: { color: '#ef4444' } },
        { name: 'Variable',     type: 'bar', stack: 'expense', data: s.variable,   itemStyle: { color: '#f97316' } },
        { name: 'Guilt-free',   type: 'bar', stack: 'expense', data: s.guiltFree,  itemStyle: { color: '#eab308' } },
        { name: 'Savings',      type: 'bar', stack: 'expense', data: s.savings,    itemStyle: { color: '#3b82f6' } },
        { name: 'Investments',  type: 'bar', stack: 'expense', data: s.investments,itemStyle: { color: '#8b5cf6' } },
        {
          name: 'Income', type: 'line', data: s.income,
          lineStyle: { color: '#16a34a', width: 2 },
          itemStyle: { color: '#16a34a' },
        },
      ],
    };
  }

  onMount(async () => {
    const echarts = await import('echarts');
    chart = echarts.init(el);
    chart.setOption(buildOption(series));
  });

  $effect(() => {
    if (chart) chart.setOption(buildOption(series));
  });

  onDestroy(() => chart?.dispose());
</script>

<div bind:this={el} style="width:100%;height:380px;"></div>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/CashFlowChart.svelte
git commit -m "feat: CashFlowChart ECharts stacked bar + income line"
```

---

### Task 20: Step 2 — Budget & Income

**Files:** `frontend/src/routes/step2/+page.svelte`

- [ ] **Step 1: Write `frontend/src/routes/step2/+page.svelte`**

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  import { plan, markDirty } from '$lib/store.svelte';
  import SegmentEditor from '$lib/components/SegmentEditor.svelte';
  import LineItemEditor from '$lib/components/LineItemEditor.svelte';
  import CashFlowChart from '$lib/components/CashFlowChart.svelte';
  import { buildCashFlowSeries } from '$lib/cashflow';
  import type { RemainderCategory } from '$lib/types';

  const remainderOptions: { value: RemainderCategory; label: string }[] = [
    { value: 'fixed',       label: 'Fixed Expenses' },
    { value: 'variable',    label: 'Variable Expenses' },
    { value: 'guiltFree',   label: 'Guilt-free Spending' },
    { value: 'savings',     label: 'Savings' },
    { value: 'investments', label: 'Investments' },
  ];

  let series = $derived(
    buildCashFlowSeries(plan.profile.currentAge, plan.income, plan.expenses)
  );

  function next() { markDirty(); goto('/step3'); }
</script>

<h2>Step 2 — Budget & Income</h2>

<section>
  <h3>Income</h3>
  <p class="hint">Enter your salary, pension, or other income. Use segments for step changes (e.g. 80k until age 55, then 50k).</p>
  <SegmentEditor bind:segments={plan.income} />
</section>

<section>
  <h3>Expenses</h3>
  {#each [
    { key: 'fixed',       label: 'Fixed Expenses',       ph: 'e.g. Rent' },
    { key: 'variable',    label: 'Variable Expenses',    ph: 'e.g. Groceries' },
    { key: 'guiltFree',   label: 'Guilt-free Spending',  ph: 'e.g. Restaurants' },
    { key: 'savings',     label: 'Savings',              ph: 'e.g. Emergency fund' },
    { key: 'investments', label: 'Investments',          ph: 'e.g. ETF contribution' },
  ] as cat}
    <details>
      <summary>{cat.label}</summary>
      <LineItemEditor bind:items={plan.expenses[cat.key as keyof typeof plan.expenses]} placeholder={cat.ph} />
    </details>
  {/each}
</section>

<section>
  <h3>Unallocated remainder goes to</h3>
  <select bind:value={plan.remainderTo}>
    {#each remainderOptions as opt}
      <option value={opt.value}>{opt.label}</option>
    {/each}
  </select>
</section>

<section>
  <h3>Cash Flow Preview</h3>
  <CashFlowChart {series} />
</section>

<div class="nav">
  <button class="secondary" onclick={() => goto('/step1')}>← Goals</button>
  <button onclick={next}>Asset Allocation →</button>
</div>

<style>
  h2 { margin-bottom: 0.25rem; }
  section { margin-bottom: 2rem; }
  h3 { margin-bottom: 0.5rem; }
  .hint { color: #6b7280; font-size: 0.875rem; margin-bottom: 1rem; }
  details { margin-bottom: 0.75rem; }
  summary { cursor: pointer; font-weight: 600; padding: 0.5rem 0; }
  select { padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; }
  .nav { display: flex; gap: 1rem; margin-top: 1rem; }
  button { padding: 0.7rem 1.4rem; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; }
  button.secondary { background: #e5e7eb; color: #374151; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/routes/step2/+page.svelte
git commit -m "feat: step 2 budget and income page with live chart"
```

---

### Task 21: Step 3 — Asset Allocation

**Files:** `frontend/src/routes/step3/+page.svelte`

- [ ] **Step 1: Write `frontend/src/routes/step3/+page.svelte`**

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  import { plan, markDirty } from '$lib/store.svelte';

  let total = $derived(
    plan.allocation.equities + plan.allocation.bonds + plan.allocation.cash + plan.allocation.other
  );
  let valid = $derived(Math.abs(total - 100) < 0.01);

  function next() { if (!valid) return; markDirty(); goto('/step4'); }
</script>

<h2>Step 3 — Asset Allocation</h2>
<p>Set how your portfolio is invested. Weights must sum to 100%.</p>

<div class="grid">
  {#each [
    { key: 'equities', label: 'Equities' },
    { key: 'bonds',    label: 'Bonds' },
    { key: 'cash',     label: 'Cash' },
    { key: 'other',    label: 'Other' },
  ] as field}
    <label>
      {field.label}
      <div class="input-wrap">
        <input type="number" min="0" max="100" step="1"
          bind:value={plan.allocation[field.key as keyof typeof plan.allocation]} />
        <span>%</span>
      </div>
    </label>
  {/each}
</div>

<p class="total" class:error={!valid}>Total: {total.toFixed(1)}%{valid ? ' ✓' : ' — must equal 100%'}</p>

<div class="nav">
  <button class="secondary" onclick={() => goto('/step2')}>← Budget</button>
  <button onclick={next} disabled={!valid}>Run Simulation →</button>
</div>

<style>
  h2 { margin-bottom: 0.5rem; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; max-width: 400px; margin: 1.5rem 0; }
  label { display: flex; flex-direction: column; gap: 0.4rem; font-weight: 500; }
  .input-wrap { display: flex; align-items: center; gap: 0.4rem; }
  input { width: 5rem; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; text-align: right; }
  .total { font-weight: 600; color: #16a34a; }
  .total.error { color: #dc2626; }
  .nav { display: flex; gap: 1rem; margin-top: 1.5rem; }
  button { padding: 0.7rem 1.4rem; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; }
  button.secondary { background: #e5e7eb; color: #374151; }
  button:disabled { background: #9ca3af; cursor: not-allowed; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/routes/step3/+page.svelte
git commit -m "feat: step 3 asset allocation page"
```

---

### Task 22: FanChart and RuinGauge components

**Files:** `frontend/src/lib/components/FanChart.svelte`, `frontend/src/lib/components/RuinGauge.svelte`

- [ ] **Step 1: Write `frontend/src/lib/components/FanChart.svelte`**

The fan chart stacks transparent area bands between quantile pairs (p1→p5, p5→p10, etc.) using ECharts line series with `areaStyle`. The p50 median is a solid line.

```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { AgeQuantiles } from '$lib/types';

  let { data }: { data: AgeQuantiles[] } = $props();

  let el: HTMLDivElement;
  let chart: any;

  function buildOption(data: AgeQuantiles[]) {
    const ages = data.map(d => d.age);
    const pick = (key: keyof AgeQuantiles) => data.map(d => d[key] as number);
    const diff = (hi: (keyof AgeQuantiles), lo: (keyof AgeQuantiles)) =>
      data.map(d => Math.max(0, (d[hi] as number) - (d[lo] as number)));

    const bands: { name: string; base: keyof AgeQuantiles; diff: keyof AgeQuantiles; color: string; opacity: number }[] = [
      { name: 'p1',     base: 'p1',  diff: 'p1',  color: '#bfdbfe', opacity: 0 },
      { name: 'p1–p5',  base: 'p1',  diff: 'p5',  color: '#bfdbfe', opacity: 0.4 },
      { name: 'p5–p10', base: 'p5',  diff: 'p10', color: '#93c5fd', opacity: 0.5 },
      { name: 'p10–p25',base: 'p10', diff: 'p25', color: '#60a5fa', opacity: 0.5 },
      { name: 'p25–p75',base: 'p25', diff: 'p75', color: '#3b82f6', opacity: 0.3 },
      { name: 'p75–p90',base: 'p75', diff: 'p90', color: '#60a5fa', opacity: 0.5 },
      { name: 'p90–p95',base: 'p90', diff: 'p95', color: '#93c5fd', opacity: 0.5 },
      { name: 'p95–p99',base: 'p95', diff: 'p99', color: '#bfdbfe', opacity: 0.4 },
    ];

    const series: any[] = [];
    // Base invisible line for stacking
    series.push({ name: 'base', type: 'line', data: pick('p1'), lineStyle: { opacity: 0 }, stack: 'fan', areaStyle: { opacity: 0 }, symbol: 'none' });
    for (const b of bands.slice(1)) {
      series.push({
        name: b.name, type: 'line',
        data: diff(b.diff, b.base),
        stack: 'fan',
        lineStyle: { opacity: 0 },
        areaStyle: { color: b.color, opacity: b.opacity },
        symbol: 'none',
        tooltip: { show: false },
      });
    }
    // Median line
    series.push({
      name: 'Median (p50)', type: 'line', data: pick('p50'), z: 10,
      lineStyle: { color: '#1d4ed8', width: 2.5 }, itemStyle: { color: '#1d4ed8' }, symbol: 'none',
    });

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const d = data[params[0]?.dataIndex];
          if (!d) return '';
          const fmt = (v: number) => `CHF ${v.toLocaleString('de-CH', { maximumFractionDigits: 0 })}`;
          return `<b>Age ${d.age}</b><br>
            p99: ${fmt(d.p99)}<br>p95: ${fmt(d.p95)}<br>p90: ${fmt(d.p90)}<br>
            p75: ${fmt(d.p75)}<br><b>p50: ${fmt(d.p50)}</b><br>
            p25: ${fmt(d.p25)}<br>p10: ${fmt(d.p10)}<br>p5: ${fmt(d.p5)}<br>p1: ${fmt(d.p1)}`;
        },
      },
      xAxis: { type: 'category', data: ages, name: 'Age' },
      yAxis: { type: 'value', axisLabel: { formatter: (v: number) => `${(v/1000).toFixed(0)}k` } },
      legend: { show: false },
      series,
    };
  }

  onMount(async () => {
    const echarts = await import('echarts');
    chart = echarts.init(el);
    chart.setOption(buildOption(data));
  });

  $effect(() => { if (chart) chart.setOption(buildOption(data), true); });
  onDestroy(() => chart?.dispose());
</script>

<div bind:this={el} style="width:100%;height:420px;"></div>
```

- [ ] **Step 2: Write `frontend/src/lib/components/RuinGauge.svelte`**

```svelte
<script lang="ts">
  let { probability }: { probability: number } = $props();

  let pct = $derived(Math.round(probability * 100));
  let color = $derived(
    pct <= 5 ? '#16a34a' : pct <= 15 ? '#ca8a04' : pct <= 30 ? '#ea580c' : '#dc2626'
  );
  let label = $derived(
    pct <= 5 ? 'Very low risk' : pct <= 15 ? 'Moderate risk' : pct <= 30 ? 'High risk' : 'Critical risk'
  );
</script>

<div class="gauge">
  <div class="circle" style="--color:{color}">
    <span class="pct">{pct}%</span>
    <span class="sub">ruin probability</span>
  </div>
  <p class="label" style="color:{color}">{label}</p>
  <p class="desc">Fraction of simulated futures where net worth reached zero at any point.</p>
</div>

<style>
  .gauge { text-align: center; }
  .circle {
    width: 160px; height: 160px; border-radius: 50%;
    border: 8px solid var(--color);
    display: inline-flex; flex-direction: column;
    align-items: center; justify-content: center; margin: 1rem 0;
  }
  .pct { font-size: 2.5rem; font-weight: 700; color: var(--color); line-height: 1; }
  .sub { font-size: 0.7rem; color: #6b7280; }
  .label { font-weight: 600; font-size: 1.1rem; margin-bottom: 0.25rem; }
  .desc { font-size: 0.8rem; color: #6b7280; max-width: 280px; margin: 0 auto; }
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/FanChart.svelte frontend/src/lib/components/RuinGauge.svelte
git commit -m "feat: FanChart and RuinGauge components"
```

---

### Task 23: Step 4 — Simulation results

**Files:** `frontend/src/routes/step4/+page.svelte`

- [ ] **Step 1: Write `frontend/src/routes/step4/+page.svelte`**

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  import { plan, clearSimulation } from '$lib/store.svelte';
  import { simulate } from '$lib/api';
  import FanChart from '$lib/components/FanChart.svelte';
  import RuinGauge from '$lib/components/RuinGauge.svelte';
  import CashFlowChart from '$lib/components/CashFlowChart.svelte';
  import { buildCashFlowSeries } from '$lib/cashflow';

  let loading = $state(false);
  let error = $state<string | null>(null);

  // Build cash flow series including simulated investment returns for Step 4 chart.
  // For simplicity in v1, show the same cash flow chart as Step 2 (without per-path returns).
  // The fan chart captures the investment return impact on net worth.
  let cashFlowSeries = $derived(
    buildCashFlowSeries(plan.profile.currentAge, plan.income, plan.expenses)
  );

  async function runSimulation() {
    loading = true;
    error = null;
    try {
      plan.simulationResult = await simulate(plan);
      plan.isDirty = false;
    } catch (e: any) {
      error = e.message ?? 'Simulation failed';
    } finally {
      loading = false;
    }
  }

  // Auto-run on first visit if no result yet
  import { onMount } from 'svelte';
  onMount(() => { if (!plan.simulationResult) runSimulation(); });
</script>

<h2>Step 4 — Simulation Results</h2>

{#if plan.isDirty}
  <div class="banner warning">
    Parameters changed since last simulation.
    <button onclick={runSimulation}>Re-run simulation</button>
  </div>
{/if}

{#if error}
  <div class="banner error">
    {error}
    <button onclick={() => error = null}>✕</button>
  </div>
{/if}

{#if loading}
  <p class="loading">Running simulation…</p>
{:else if plan.simulationResult}
  <section>
    <h3>Net Worth Projection</h3>
    <FanChart data={plan.simulationResult.byAge} />
  </section>

  <section class="ruin-section">
    <h3>Probability of Ruin</h3>
    <RuinGauge probability={plan.simulationResult.ruinProbability} />
  </section>

  <section>
    <h3>Cash Flow (with investment returns)</h3>
    <CashFlowChart series={cashFlowSeries} />
  </section>
{/if}

<div class="nav">
  <button class="secondary" onclick={() => goto('/step3')}>← Allocation</button>
  {#if !loading}
    <button onclick={runSimulation}>↺ Re-run</button>
  {/if}
</div>

<style>
  h2 { margin-bottom: 0.5rem; }
  section { margin-bottom: 2.5rem; }
  h3 { margin-bottom: 0.75rem; }
  .banner { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1.5rem; }
  .banner.warning { background: #fef9c3; color: #713f12; }
  .banner.error { background: #fee2e2; color: #991b1b; }
  .banner button { background: none; border: none; cursor: pointer; font-weight: 600; text-decoration: underline; color: inherit; }
  .loading { color: #6b7280; font-style: italic; margin: 2rem 0; }
  .ruin-section { text-align: center; }
  .nav { display: flex; gap: 1rem; margin-top: 1rem; }
  button { padding: 0.7rem 1.4rem; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; }
  button.secondary { background: #e5e7eb; color: #374151; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/routes/step4/+page.svelte
git commit -m "feat: step 4 simulation results page"
```

---

### Task 24: Frontend store and cashflow tests

**Files:** `frontend/src/lib/cashflow.test.ts`

- [ ] **Step 1: Write `frontend/src/lib/cashflow.test.ts`**

```typescript
import { describe, it, expect } from 'vitest';
import { expandSegments, expandLineItems, buildCashFlowSeries } from './cashflow';
import type { Segment, LineItem, Expenses } from './types';

const seg = (value: number, opts: Partial<Segment> = {}): Segment =>
  ({ value, until: null, oneOff: false, ...opts });

const item = (label: string, ...segs: Segment[]): LineItem => ({ label, segments: segs });

describe('expandSegments', () => {
  it('single indefinite segment fills all years', () => {
    expect(expandSegments([seg(1000)], 30, 3)).toEqual([1000, 1000, 1000]);
  });

  it('segment until age stops at correct index', () => {
    const result = expandSegments([seg(500, { until: { age: 32 } })], 30, 5);
    expect(result).toEqual([500, 500, 0, 0, 0]);
  });

  it('step change applies correctly', () => {
    const segs = [seg(1000, { until: { age: 32 } }), seg(2000)];
    expect(expandSegments(segs, 30, 4)).toEqual([1000, 1000, 2000, 2000]);
  });

  it('one-off segment applies once at cursor position', () => {
    expect(expandSegments([seg(5000, { oneOff: true })], 30, 3)).toEqual([5000, 0, 0]);
  });

  it('returns zeros for empty segments', () => {
    expect(expandSegments([], 30, 3)).toEqual([0, 0, 0]);
  });
});

describe('expandLineItems', () => {
  it('sums multiple items', () => {
    const items = [item('A', seg(100)), item('B', seg(200))];
    expect(expandLineItems(items, 30, 2)).toEqual([300, 300]);
  });
});

describe('buildCashFlowSeries', () => {
  it('produces correct ages array', () => {
    const expenses: Expenses = { fixed: [], variable: [], guiltFree: [], savings: [], investments: [] };
    const s = buildCashFlowSeries(30, [], expenses, 3);
    expect(s.ages).toEqual([30, 31, 32]);
  });

  it('surplus equals income minus all expenses', () => {
    const expenses: Expenses = {
      fixed: [item('rent', seg(600))], variable: [], guiltFree: [], savings: [], investments: [],
    };
    const s = buildCashFlowSeries(30, [seg(1000)], expenses, 2);
    expect(s.income).toEqual([1000, 1000]);
    expect(s.fixed).toEqual([600, 600]);
    expect(s.surplus).toEqual([400, 400]);
  });
});
```

- [ ] **Step 2: Run tests (from frontend dir after npm install)**

```bash
cd frontend && npm install && npx vitest run src/lib/cashflow.test.ts
```

Expected: all tests pass

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/cashflow.test.ts
git commit -m "test: frontend cashflow helper unit tests"
```

---

### Task 25: Verify full Docker build

This task confirms the end-to-end build works before declaring the implementation complete.

- [ ] **Step 1: Build the Docker image**

```bash
docker compose build
```

Expected: build succeeds (Rust wheel compiled and installed, Python deps installed)

- [ ] **Step 2: Start all services**

```bash
docker compose up
```

Expected:
- Backend: `http://localhost:8000` returns `{"status":"ok"}`
- Frontend: `http://localhost:5173` shows the profile page

- [ ] **Step 3: Smoke test the API**

```bash
curl -s http://localhost:8000/ | python3 -m json.tool
```

Expected: `{"status": "ok"}`

- [ ] **Step 4: Test validate endpoint**

```bash
curl -s -X POST http://localhost:8000/api/validate \
  -H 'Content-Type: application/json' \
  -d '{"profile":{"current_age":35,"current_net_worth":100000},"income":[],"expenses":{},"goals":[],"remainder_to":"investments","allocation":{"equities":60,"bonds":30,"cash":5,"other":5}}' \
  | python3 -m json.tool
```

Expected: `{"errors": []}`

- [ ] **Step 5: Run backend tests inside container**

```bash
docker compose exec backend python -m pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "chore: verify full Docker build and smoke tests pass"
```

---

## Self-Review Against Spec

| Spec requirement | Covered by task |
|---|---|
| User profile: age + current net worth | Task 15 |
| Step 1: Goals (running + one-off, age or year) | Task 18 |
| Step 2: Income segments | Task 20 |
| Step 2: 5 expense categories with line items | Task 20 |
| Step 2: Remainder allocation to any category | Task 20 |
| Step 2: Stacked area cash flow chart with hover tooltip | Task 19, 20 |
| Step 3: Asset allocation summing to 100% | Task 21 |
| Step 4: Fan chart with p1/p5/p10/p25/p50/p75/p90/p95/p99 | Task 22 |
| Step 4: Ruin probability gauge | Task 22 |
| Step 4: Cash flow chart (repeated from Step 2) | Task 23 |
| isDirty banner + re-run prompt | Task 23 |
| Error banner (simulation/network errors) | Task 23 |
| Monte Carlo GBM engine in Rust | Task 4 |
| Deterministic tests (0%, 100%, ruin at exact age, one-off) | Task 4 |
| PyO3 bindings | Task 5 |
| Python cashflow service (segment expansion, remainder) | Task 7, 8 |
| Python cashflow tests | Task 8 |
| /api/simulate + /api/validate | Task 9 |
| Route tests with mocked rust_core | Task 10 |
| Frontend cashflow tests | Task 24 |
| Docker Compose local dev | Task 2 |
| Session-only state (no backend persistence) | All tasks |
