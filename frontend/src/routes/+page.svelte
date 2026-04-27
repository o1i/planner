<script lang="ts">
  import { goto } from '$app/navigation';
  import { plan } from '$lib/store.svelte';

  let ageStr = $state(plan.profile.currentAge ? String(plan.profile.currentAge) : '');
  let worthStr = $state(plan.profile.currentNetWorth ? String(plan.profile.currentNetWorth) : '');
  let errors = $state<{ age?: string; worth?: string }>({});

  function validate() {
    const e: typeof errors = {};
    const age = parseInt(ageStr);
    const worth = parseFloat(worthStr);
    if (!ageStr || isNaN(age) || age < 1 || age > 120) e.age = 'Enter a valid age (1–120)';
    if (!worthStr || isNaN(worth)) e.worth = 'Enter your current net worth in CHF';
    return e;
  }

  function next() {
    errors = validate();
    if (Object.keys(errors).length) return;
    plan.profile.currentAge = parseInt(ageStr);
    plan.profile.currentNetWorth = parseFloat(worthStr);
    goto('/step1');
  }
</script>

<h1>Financial Planner</h1>
<p>Let's start with a few basics about your current situation.</p>

<div class="form">
  <label>
    Your current age
    <input type="text" inputmode="numeric" bind:value={ageStr} />
    {#if errors.age}<span class="error">{errors.age}</span>{/if}
  </label>
  <label>
    Current net worth (CHF)
    <input type="text" inputmode="numeric" bind:value={worthStr} />
    {#if errors.worth}<span class="error">{errors.worth}</span>{/if}
  </label>
  <button onclick={next}>Start planning →</button>
</div>

<style>
  h1 { font-size: 2rem; margin-bottom: 0.5rem; }
  .form { display: flex; flex-direction: column; gap: 1.25rem; max-width: 360px; margin-top: 2rem; }
  label { display: flex; flex-direction: column; gap: 0.4rem; font-weight: 500; }
  input { padding: 0.6rem 0.75rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: 1rem; }
  .error { color: #dc2626; font-size: 0.8rem; }
  button { padding: 0.75rem 1.5rem; background: #2563eb; color: white; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; }
  button:hover { background: #1d4ed8; }
</style>
