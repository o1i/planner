<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { AgeQuantiles } from '$lib/types';

  let { data }: { data: AgeQuantiles[] } = $props();

  let el: HTMLDivElement;
  let chart: any;

  function buildOption(data: AgeQuantiles[]) {
    const ages = data.map(d => d.age);
    const pick = (key: keyof AgeQuantiles) => data.map(d => d[key] as number);
    const diff = (hi: (keyof AgeQuantiles), lo: (keyof AgeQuantiles)) =>
      data.map(d => Math.max(0, (d[hi] as number) - (d[lo] as number)));

    const bands: { name: string; base: keyof AgeQuantiles; diff: keyof AgeQuantiles; color: string; opacity: number }[] = [
      { name: 'p1',     base: 'p1',  diff: 'p1',  color: '#bfdbfe', opacity: 0 },
      { name: 'p1–p5',  base: 'p1',  diff: 'p5',  color: '#bfdbfe', opacity: 0.4 },
      { name: 'p5–p10', base: 'p5',  diff: 'p10', color: '#93c5fd', opacity: 0.5 },
      { name: 'p10–p25',base: 'p10', diff: 'p25', color: '#60a5fa', opacity: 0.5 },
      { name: 'p25–p75',base: 'p25', diff: 'p75', color: '#3b82f6', opacity: 0.3 },
      { name: 'p75–p90',base: 'p75', diff: 'p90', color: '#60a5fa', opacity: 0.5 },
      { name: 'p90–p95',base: 'p90', diff: 'p95', color: '#93c5fd', opacity: 0.5 },
      { name: 'p95–p99',base: 'p95', diff: 'p99', color: '#bfdbfe', opacity: 0.4 },
    ];

    const series: any[] = [];
    // Base invisible line for stacking
    series.push({ name: 'base', type: 'line', data: pick('p1'), lineStyle: { opacity: 0 }, stack: 'fan', areaStyle: { opacity: 0 }, symbol: 'none' });
    for (const b of bands.slice(1)) {
      series.push({
        name: b.name, type: 'line',
        data: diff(b.diff, b.base),
        stack: 'fan',
        lineStyle: { opacity: 0 },
        areaStyle: { color: b.color, opacity: b.opacity },
        symbol: 'none',
        tooltip: { show: false },
      });
    }
    // Median line
    series.push({
      name: 'Median (p50)', type: 'line', data: pick('p50'), z: 10,
      lineStyle: { color: '#1d4ed8', width: 2.5 }, itemStyle: { color: '#1d4ed8' }, symbol: 'none',
    });

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const d = data[params[0]?.dataIndex];
          if (!d) return '';
          const fmt = (v: number) => `CHF ${v.toLocaleString('de-CH', { maximumFractionDigits: 0 })}`;
          return `<b>Age ${d.age}</b><br>
            p99: ${fmt(d.p99)}<br>p95: ${fmt(d.p95)}<br>p90: ${fmt(d.p90)}<br>
            p75: ${fmt(d.p75)}<br><b>p50: ${fmt(d.p50)}</b><br>
            p25: ${fmt(d.p25)}<br>p10: ${fmt(d.p10)}<br>p5: ${fmt(d.p5)}<br>p1: ${fmt(d.p1)}`;
        },
      },
      xAxis: { type: 'category', data: ages, name: 'Age' },
      yAxis: { type: 'value', axisLabel: { formatter: (v: number) => `${(v/1000).toFixed(0)}k` } },
      legend: { show: false },
      series,
    };
  }

  onMount(async () => {
    const echarts = await import('echarts');
    chart = echarts.init(el);
    chart.setOption(buildOption(data));
  });

  $effect(() => { if (chart) chart.setOption(buildOption(data), true); });
  onDestroy(() => chart?.dispose());
</script>

<div bind:this={el} style="width:100%;height:420px;"></div>
