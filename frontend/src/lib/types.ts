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
