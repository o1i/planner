<script lang="ts">
  import type { Segment } from '$lib/types';

  let { segments = $bindable() }: { segments: Segment[] } = $props();

  function addSegment() {
    segments = [...segments, { value: 0, until: null, oneOff: false }];
  }

  function remove(i: number) {
    segments = segments.filter((_, idx) => idx !== i);
  }

  function setUntilType(i: number, type: 'none' | 'age' | 'year') {
    const seg = { ...segments[i] };
    seg.until = type === 'none' ? null : type === 'age' ? { age: 0 } : { year: new Date().getFullYear() + 1 };
    segments = segments.map((s, idx) => idx === i ? seg : s);
  }

  function untilType(seg: Segment): 'none' | 'age' | 'year' {
    if (!seg.until) return 'none';
    return 'age' in seg.until ? 'age' : 'year';
  }
</script>

<div class="segment-editor">
  {#each segments as seg, i}
    <div class="row">
      <input type="number" placeholder="CHF/year" bind:value={seg.value} />
      <label class="one-off">
        <input type="checkbox" bind:checked={seg.oneOff} /> One-off
      </label>
      <select value={untilType(seg)} onchange={e => setUntilType(i, (e.target as HTMLSelectElement).value as 'none' | 'age' | 'year')}>
        <option value="none">Indefinite</option>
        <option value="age">Until age</option>
        <option value="year">Until year</option>
      </select>
      {#if seg.until && 'age' in seg.until}
        <input type="number" placeholder="Age" bind:value={seg.until.age} min="0" max="120" />
      {:else if seg.until && 'year' in seg.until}
        <input type="number" placeholder="Year" bind:value={seg.until.year} />
      {/if}
      <button class="remove" onclick={() => remove(i)}>✕</button>
    </div>
  {/each}
  <button class="add" onclick={addSegment}>+ Add segment</button>
</div>

<style>
  .segment-editor { display: flex; flex-direction: column; gap: 0.5rem; }
  .row { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
  input[type=number] { width: 8rem; padding: 0.4rem 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; }
  select { padding: 0.4rem 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; }
  .one-off { display: flex; align-items: center; gap: 0.3rem; font-size: 0.85rem; }
  .remove { background: none; border: none; color: #6b7280; cursor: pointer; font-size: 1rem; }
  .add { margin-top: 0.25rem; background: none; border: 1px dashed #9ca3af; color: #6b7280; padding: 0.35rem 0.75rem; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
</style>
