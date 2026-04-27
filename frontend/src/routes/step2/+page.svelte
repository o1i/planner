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

  async function next() { markDirty(); await goto('/step3'); }
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
  <button class="secondary" onclick={async () => { await goto('/step1'); }}>← Goals</button>
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
