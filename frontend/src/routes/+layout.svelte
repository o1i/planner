<script lang="ts">
  import { page } from '$app/stores';
  import WizardNav from '$lib/components/WizardNav.svelte';

  const stepMap: Record<string, 1 | 2 | 3 | 4> = {
    '/step1': 1, '/step2': 2, '/step3': 3, '/step4': 4,
  };
  let currentStep = $derived(stepMap[$page.url.pathname] ?? 0 as any);
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
