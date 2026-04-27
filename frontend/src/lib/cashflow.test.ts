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
