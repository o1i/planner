<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { plan, clearSimulation } from '$lib/store.svelte';
  import { simulate } from '$lib/api';
  import FanChart from '$lib/components/FanChart.svelte';
  import RuinGauge from '$lib/components/RuinGauge.svelte';
  import CashFlowChart from '$lib/components/CashFlowChart.svelte';
  import { buildCashFlowSeries } from '$lib/cashflow';

  let loading = $state(false);
  let error = $state<string | null>(null);

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
  <button class="secondary" onclick={async () => { await goto('/step3'); }}>← Allocation</button>
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
