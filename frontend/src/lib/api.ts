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
