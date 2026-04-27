import type { PlanState } from './types';

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
