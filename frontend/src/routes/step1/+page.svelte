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
