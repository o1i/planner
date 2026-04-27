<script lang="ts">
  let { probability }: { probability: number } = $props();

  let pct = $derived(Math.round(probability * 100));
  let color = $derived(
    pct <= 5 ? '#16a34a' : pct <= 15 ? '#ca8a04' : pct <= 30 ? '#ea580c' : '#dc2626'
  );
  let label = $derived(
    pct <= 5 ? 'Very low risk' : pct <= 15 ? 'Moderate risk' : pct <= 30 ? 'High risk' : 'Critical risk'
  );
</script>

<div class="gauge">
  <div class="circle" style="--color:{color}">
    <span class="pct">{pct}%</span>
    <span class="sub">ruin probability</span>
  </div>
  <p class="label" style="color:{color}">{label}</p>
  <p class="desc">Fraction of simulated futures where net worth reached zero at any point.</p>
</div>

<style>
  .gauge { text-align: center; }
  .circle {
    width: 160px; height: 160px; border-radius: 50%;
    border: 8px solid var(--color);
    display: inline-flex; flex-direction: column;
    align-items: center; justify-content: center; margin: 1rem 0;
  }
  .pct { font-size: 2.5rem; font-weight: 700; color: var(--color); line-height: 1; }
  .sub { font-size: 0.7rem; color: #6b7280; }
  .label { font-weight: 600; font-size: 1.1rem; margin-bottom: 0.25rem; }
  .desc { font-size: 0.8rem; color: #6b7280; max-width: 280px; margin: 0 auto; }
</style>
