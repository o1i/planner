# Financial Planner — Design Spec
_2026-04-26_

## Overview

A guided 4-step web application that walks users through a complete personal financial plan: defining goals, modelling income and expenses, setting asset allocation, and running a Monte Carlo simulation of future net worth outcomes. Designed for personal/small-group use (≤ 3 concurrent users). Currency: CHF.

---

## Architecture

```
┌─────────────────────────────────┐
│  SvelteKit Frontend             │
│  (browser, session state)       │
│                                 │
│  Step 1: Goals                  │
│  Step 2: Budgets & Income       │
│  Step 3: Asset Allocation       │
│  Step 4: Simulation + Charts    │
└────────────┬────────────────────┘
             │ HTTP REST (JSON)
             ▼
┌─────────────────────────────────┐
│  FastAPI Backend (Python)       │
│  POST /api/simulate             │
│  POST /api/validate             │
└────────────┬────────────────────┘
             │ PyO3 FFI
             ▼
┌─────────────────────────────────┐
│  Rust Library (rust_core)       │
│  - Monte Carlo engine           │
│  - Return path sampling         │
│  - Ruin probability calc        │
└─────────────────────────────────┘
```

**Key principles:**
- All wizard state lives in the SvelteKit frontend (a single reactive store). The backend is stateless in v1.
- Python handles HTTP, data wrangling, and cash flow computation. Rust handles simulation only.
- Docker Compose runs both services locally in development (frontend: `localhost:5173`, backend: `localhost:8000`).
- Future persistence (user accounts, saved plans) requires only adding save/load endpoints — no structural changes.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | SvelteKit 5, TypeScript, ECharts |
| Backend | Python, FastAPI, uvicorn |
| Simulation | Rust (PyO3 extension, compiled into Python wheel) |
| Dev environment | Docker Compose |
| Frontend deployment | Cloudflare Pages |
| Backend deployment | Fly.io / Railway (TBD) |

---

## Frontend Design

### User Profile

Collected before the wizard starts: **current age**. Used to convert all age-based time entries to calendar years and vice versa.

### Wizard Steps

A persistent top progress bar shows the four steps. The user can navigate back freely. Going back does not clear later steps — it sets `isDirty = true`, which shows a "parameters changed — re-run simulation" banner on Step 4.

### Time-Varying Entries

All income, expense, and goal entries share the same **segment model**: a list of segments, each with a value and an end point expressed as either an **age** or an **absolute year**. One-off entries are a segment of duration 1.

Examples:
- Income: `100k until age 55 → 150k until age 60 → 0`
- Goal (running): `20k/year from age 65 onwards`
- Goal (one-off): `100k at age 45`
- Expense (one-off): `50k home repair in 2031`

### Step 1 — Goals

Users define financial goals as either:
- **Running costs**: an amount per year for a period (e.g. "Travel: 20k/year from age 65")
- **One-offs**: a lump sum at a specific age or year (e.g. "Home renovation: 100k at age 50")

### Step 2 — Budget & Income

**Income**: Entered as CHF amounts using the segment model (step changes over time, age or year).

**Expenses**: Entered as absolute CHF line items, grouped into five categories. Each line item uses the segment model.

| Category | Example items |
|---|---|
| Fixed Expenses | Rent 1000, Insurance 200 |
| Variable Expenses | Groceries 500, Transport 150 |
| Guilt-free Spending | Restaurants 100, Hobbies 200 |
| Savings | Emergency fund 300 |
| Investments | ETF contribution 800 |

**Remainder**: Income minus total categorised expenses = remainder. The user explicitly chooses which of the five categories the remainder is allocated to.

**Step 2 chart — Cash Flow Preview**: A stacked area chart showing the five expense categories (in CHF) over time (by age), with a line overlay for income (excluding investment returns). A highlighted delta band shows surplus/deficit. Hovering over any age reveals a tooltip with all values for that age.

### Step 3 — Asset Allocation

User sets percentage allocation across: Equities, Bonds, Cash, Other. Must sum to 100%.

### Step 4 — Simulation Results

After running the simulation, Step 4 shows three charts:

1. **Fan chart**: Net worth by age with quantile bands (p1, p5, p10, p25, p50, p75, p90, p95, p99). Hover tooltip shows all quantile values at each age.
2. **Ruin probability gauge**: Fraction of simulation paths that reach net worth ≤ 0 at any point. Displayed prominently with a green-to-red color scale.
3. **Cash flow chart**: The same stacked area chart from Step 2, but with investment returns now included in the income line — showing how the picture changes with portfolio growth.

When the user navigates back and changes any input, a banner prompts them to re-run the simulation.

### State Model

```typescript
interface Segment {
  value: number        // CHF per year
  until: { age: number } | { year: number } | null  // null = indefinite
  oneOff: boolean
}

interface LineItem {
  label: string
  segments: Segment[]
}

interface SimulationResult {
  byAge: {
    age: number
    p1: number; p5: number; p10: number; p25: number; p50: number
    p75: number; p90: number; p95: number; p99: number
  }[]
  ruinProbability: number
}

interface PlanStore {
  profile: { currentAge: number }
  goals: LineItem[]
  income: Segment[]
  expenses: {
    fixed:       LineItem[]
    variable:    LineItem[]
    guiltFree:   LineItem[]
    savings:     LineItem[]
    investments: LineItem[]
  }
  remainderTo: 'fixed' | 'variable' | 'guiltFree' | 'savings' | 'investments'
  allocation: { equities: number; bonds: number; cash: number; other: number }
  simulationResult: SimulationResult | null
  isDirty: boolean
}
```

---

## Backend Design

### FastAPI Layer (Python)

Thin orchestration — no simulation logic.

**`POST /api/simulate`**

Receives the full plan. Python:
1. Expands all segments into a per-age cash flow vector (CHF net cash flow per year)
2. Applies remainder allocation
3. Passes the numerical inputs to the Rust engine
4. Returns `SimulationResult`

**`POST /api/validate`**

Lightweight checks called on-the-fly as the user fills in the wizard:
- Allocation sums to 100%
- No negative ages or years
- Segments are non-overlapping and ordered

Returns field-level validation errors for inline display in the wizard.

### Rust Engine (`rust_core` via PyO3)

**Inputs** (from Python):
- `cash_flows: Vec<f64>` — net CHF cash flow per year (index 0 = current age)
- `allocation: [f64; 4]` — equities, bonds, cash, other weights
- `return_assumptions: [(f64, f64); 4]` — (expected annual return, volatility) per asset class
- `num_paths: usize` — number of simulation paths (default 10,000)
- `current_age: u32`

**Output**:
- Per-age quantiles: p1, p5, p10, p25, p50, p75, p90, p95, p99
- `ruin_probability: f64` — fraction of paths reaching net worth ≤ 0 at any point

**Simulation method (v1)**: Geometric Brownian motion with correlated asset returns. Return assumptions are hardcoded defaults in v1 (equities 7%/15%, bonds 3%/5%, cash 0.5%/0.5%, other 5%/10%) — exposed as parameters so they can be made user-configurable later.

**Future simulation upgrade**: Switching to bootstrapped historical return sequences is a change entirely internal to `rust_core`. Python passes the same inputs; Rust's internal sampling method changes. The only anticipated interface addition is an optional `historical_returns` dataset passed through transparently by Python.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Validation error (e.g. allocation ≠ 100%) | Inline field error in the wizard step, surfaced via `/api/validate` |
| Simulation error (Rust panic, malformed input) | FastAPI returns 500; frontend shows dismissable banner on Step 4 with "try again" |
| Network error (backend unreachable) | Frontend banner; wizard state is never lost (lives in browser store) |

---

## Testing

### Rust — Deterministic unit tests

All tests use a fixed random seed. Key test cases with human-verifiable expected outputs:

| Scenario | Expected result |
|---|---|
| 0% return, income > expenses (fixed) | Net worth grows linearly; all paths identical; ruin probability = 0; all quantiles equal deterministic value |
| 100% return, fixed income | Net worth doubles each year; all paths identical |
| 0% return, income < expenses (fixed) | Net worth declines linearly; ruin at exactly the calculable age; all quantiles identical |
| Zero income, large one-off expense at age X | Net worth drops sharply at exactly age X across all paths |

### Python — Unit tests (pytest)

- Segment expansion: verify cash flow vector is correctly computed from segments
- Remainder allocation: verify unallocated income lands in the correct category
- CHF arithmetic: rounding and precision edge cases

### Frontend — Component tests

- Wizard navigation (forward, back, `isDirty` flag)
- Store logic (segment model, remainder calculation)
- No E2E tests in v1

---

## Future Considerations (out of scope for v1)

- User accounts and plan persistence (server-side storage)
- Configurable return/volatility assumptions per asset class
- Historical return bootstrapping in the Rust engine
- Inflation adjustment
- Tax modelling
