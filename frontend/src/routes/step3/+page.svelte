<script lang="ts">
  import { goto } from '$app/navigation';
  import { plan, markDirty } from '$lib/store.svelte';

  let total = $derived(
    plan.allocation.equities + plan.allocation.bonds + plan.allocation.cash + plan.allocation.other
  );
  let valid = $derived(Math.abs(total - 100) < 0.01);

  async function next() { if (!valid) return; markDirty(); await goto('/step4'); }
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
  <button class="secondary" onclick={async () => { await goto('/step2'); }}>← Budget</button>
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
