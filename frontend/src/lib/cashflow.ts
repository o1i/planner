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
      const end = seg.until === null ? nYears : Math.min(Math.max(untilToIndex(seg.until, currentAge), cursor), nYears);
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
