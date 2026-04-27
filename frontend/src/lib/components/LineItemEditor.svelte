<script lang="ts">
  import type { LineItem } from '$lib/types';
  import SegmentEditor from './SegmentEditor.svelte';

  let { items = $bindable(), placeholder = 'e.g. Rent' }: { items: LineItem[]; placeholder?: string } = $props();

  function addItem() {
    items = [...items, { label: '', segments: [{ value: 0, until: null, oneOff: false }] }];
  }

  function remove(i: number) {
    items = items.filter((_, idx) => idx !== i);
  }
</script>

<div class="line-item-editor">
  {#each items as item, i}
    <div class="item-block">
      <div class="item-header">
        <input class="label-input" type="text" placeholder={placeholder} bind:value={item.label} />
        <button class="remove" onclick={() => remove(i)}>Remove</button>
      </div>
      <SegmentEditor bind:segments={item.segments} />
    </div>
  {/each}
  <button class="add" onclick={addItem}>+ Add item</button>
</div>

<style>
  .line-item-editor { display: flex; flex-direction: column; gap: 1rem; }
  .item-block { border: 1px solid #e5e7eb; border-radius: 6px; padding: 0.75rem; }
  .item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
  .label-input { font-weight: 600; border: none; border-bottom: 1px solid #d1d5db; padding: 0.2rem; font-size: 0.95rem; width: 14rem; }
  .remove { background: none; border: none; color: #ef4444; cursor: pointer; font-size: 0.8rem; }
  .add { background: none; border: 1px dashed #9ca3af; color: #6b7280; padding: 0.4rem 0.9rem; border-radius: 4px; cursor: pointer; }
</style>
