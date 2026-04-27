<script lang="ts">
  let { currentStep }: { currentStep: 1 | 2 | 3 | 4 } = $props();
  const steps = ['Profile', 'Goals', 'Budget & Income', 'Allocation', 'Simulation'];
  // Step 0 = profile (not numbered), steps 1-4 = wizard
</script>

<nav class="wizard-nav">
  {#each [1, 2, 3, 4] as n}
    <div class="step" class:active={currentStep === n} class:done={currentStep > n}>
      <span class="circle">{n}</span>
      <span class="label">{steps[n]}</span>
    </div>
    {#if n < 4}<div class="connector" class:filled={currentStep > n}></div>{/if}
  {/each}
</nav>

<style>
  .wizard-nav { display: flex; align-items: center; padding: 1.5rem 2rem; gap: 0; }
  .step { display: flex; align-items: center; gap: 0.5rem; }
  .circle {
    width: 2rem; height: 2rem; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 600; font-size: 0.85rem;
    background: #e5e7eb; color: #6b7280;
  }
  .step.active .circle { background: #2563eb; color: white; }
  .step.done .circle { background: #16a34a; color: white; }
  .label { font-size: 0.875rem; color: #374151; }
  .step.active .label { color: #2563eb; font-weight: 600; }
  .connector { flex: 1; height: 2px; background: #e5e7eb; min-width: 2rem; margin: 0 0.5rem; }
  .connector.filled { background: #16a34a; }
</style>
