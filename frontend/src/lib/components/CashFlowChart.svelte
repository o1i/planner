<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { CashFlowSeries } from '$lib/cashflow';

  let { series }: { series: CashFlowSeries } = $props();

  let el: HTMLDivElement;
  let chart: any;

  function buildOption(s: CashFlowSeries) {
    const fmt = (v: number) => `CHF ${v.toLocaleString('de-CH', { maximumFractionDigits: 0 })}`;
    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const age = params[0]?.axisValue;
          return `<b>Age ${age}</b><br>` + params.map(p => `${p.seriesName}: ${fmt(p.value)}`).join('<br>');
        },
      },
      legend: { bottom: 0 },
      xAxis: { type: 'category', data: s.ages, name: 'Age' },
      yAxis: { type: 'value', axisLabel: { formatter: (v: number) => `${(v/1000).toFixed(0)}k` } },
      series: [
        { name: 'Fixed',        type: 'bar', stack: 'expense', data: s.fixed,      itemStyle: { color: '#ef4444' } },
        { name: 'Variable',     type: 'bar', stack: 'expense', data: s.variable,   itemStyle: { color: '#f97316' } },
        { name: 'Guilt-free',   type: 'bar', stack: 'expense', data: s.guiltFree,  itemStyle: { color: '#eab308' } },
        { name: 'Savings',      type: 'bar', stack: 'expense', data: s.savings,    itemStyle: { color: '#3b82f6' } },
        { name: 'Investments',  type: 'bar', stack: 'expense', data: s.investments,itemStyle: { color: '#8b5cf6' } },
        {
          name: 'Income', type: 'line', data: s.income,
          lineStyle: { color: '#16a34a', width: 2 },
          itemStyle: { color: '#16a34a' },
        },
      ],
    };
  }

  onMount(async () => {
    const echarts = await import('echarts');
    chart = echarts.init(el);
    chart.setOption(buildOption(series));
  });

  $effect(() => {
    if (chart) chart.setOption(buildOption(series));
  });

  onDestroy(() => chart?.dispose());
</script>

<div bind:this={el} style="width:100%;height:380px;"></div>
