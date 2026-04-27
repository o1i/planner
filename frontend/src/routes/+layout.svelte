<script lang="ts">
  import { page } from '$app/state';
  import WizardNav from '$lib/components/WizardNav.svelte';

  type WizardStep = 0 | 1 | 2 | 3 | 4;
  const stepMap: Record<string, WizardStep> = {
    '/step1': 1, '/step2': 2, '/step3': 3, '/step4': 4,
  };
  let currentStep = $derived<WizardStep>(stepMap[page.url.pathname] ?? 0);
  let showNav = $derived(currentStep >= 1);
</script>

<div class="app">
  {#if showNav}
    <WizardNav {currentStep} />
  {/if}
  <main>
    <slot />
  </main>
</div>

<style>
  .app { min-height: 100vh; font-family: system-ui, sans-serif; }
  main { max-width: 860px; margin: 0 auto; padding: 2rem; }
</style>
