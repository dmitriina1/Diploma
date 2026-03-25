<template>
  <div class="line-chart">
    <div class="lc-captions">
      <span>Ось Y: {{ yLabel }} ({{ unit }})</span>
      <span>Ось X: {{ xLabel }}</span>
    </div>
    <svg viewBox="0 0 100 42" preserveAspectRatio="none" class="lc-svg" aria-hidden="true">
      <line v-for="y in gridLines" :key="`grid-${y}`" x1="10" :y1="y" x2="98" :y2="y" class="grid" />
      <line x1="10" y1="4" x2="10" y2="36" class="axis" />
      <line x1="10" y1="36" x2="98" y2="36" class="axis" />
      <polyline :points="polylinePoints" class="line" />
      <circle v-for="p in plotted" :key="p.key" :cx="p.x" :cy="p.y" r="0.8" class="dot" />
    </svg>
    <div class="lc-scale">
      <span>{{ maxValue }} {{ unit }}</span>
      <span>{{ midValue }} {{ unit }}</span>
      <span>0 {{ unit }}</span>
    </div>
    <div class="lc-foot" v-if="plotted.length">
      <span>{{ plotted[0].label }}</span>
      <span>{{ plotted[middleIndex]?.label || plotted[0].label }}</span>
      <span>{{ plotted[plotted.length - 1].label }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  points: { type: Array, default: () => [] },
  unit: { type: String, default: 'шт' },
  xLabel: { type: String, default: 'Дата' },
  yLabel: { type: String, default: 'Значение' }
})

const maxValue = computed(() => Math.max(...props.points.map((p) => Number(p.count || 0)), 1))
const midValue = computed(() => Math.round(maxValue.value / 2))
const gridLines = [4, 12, 20, 28, 36]

const plotted = computed(() => {
  const arr = props.points || []
  if (!arr.length) return []
  const max = maxValue.value
  const startX = 10
  const endX = 98
  const step = arr.length > 1 ? (endX - startX) / (arr.length - 1) : 0
  return arr.map((p, i) => {
    const x = arr.length > 1 ? startX + (i * step) : 54
    const y = 36 - (Math.max(0, Number(p.count || 0)) / max) * 32
    return {
      key: `${p.day}-${i}`,
      x: +x.toFixed(2),
      y: +y.toFixed(2),
      label: p.day,
      value: Number(p.count || 0)
    }
  })
})

const polylinePoints = computed(() => plotted.value.map((p) => `${p.x},${p.y}`).join(' '))
const middleIndex = computed(() => Math.floor((plotted.value.length - 1) / 2))
</script>

<style scoped>
.line-chart { display: grid; gap: .45rem; }
.lc-captions, .lc-scale, .lc-foot {
  display: flex;
  justify-content: space-between;
  color: var(--c-text-4);
  font-size: .74rem;
}
.lc-scale { font-variant-numeric: tabular-nums; }
.lc-svg {
  width: 100%;
  height: 160px;
  background: color-mix(in srgb, var(--c-bg-2) 70%, transparent);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
}
.grid {
  stroke: color-mix(in srgb, var(--c-text-4) 26%, transparent);
  stroke-width: .2;
}
.axis {
  stroke: color-mix(in srgb, var(--c-text-4) 40%, transparent);
  stroke-width: .3;
}
.line {
  fill: none;
  stroke: var(--c-brand-h);
  stroke-width: 1.4;
}
.dot { fill: var(--c-accent); }
</style>
