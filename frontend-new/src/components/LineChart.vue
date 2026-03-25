<template>
  <div class="line-chart">
    <div class="lc-head">
      <span class="lc-ymax">{{ maxValue }} {{ unit }}</span>
      <span class="lc-ymin">0 {{ unit }}</span>
    </div>
    <svg viewBox="0 0 100 34" preserveAspectRatio="none" class="lc-svg" aria-hidden="true">
      <line x1="0" y1="1" x2="100" y2="1" class="axis" />
      <line x1="0" y1="33" x2="100" y2="33" class="axis" />
      <polyline :points="polylinePoints" class="line" />
      <circle v-for="p in plotted" :key="p.key" :cx="p.x" :cy="p.y" r="0.8" class="dot" />
    </svg>
    <div class="lc-foot" v-if="plotted.length">
      <span>{{ plotted[0].label }}</span>
      <span>{{ plotted[plotted.length - 1].label }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  points: { type: Array, default: () => [] },
  unit: { type: String, default: 'шт' }
})

const maxValue = computed(() => Math.max(...props.points.map((p) => Number(p.count || 0)), 1))

const plotted = computed(() => {
  const arr = props.points || []
  if (!arr.length) return []
  const max = maxValue.value
  const step = arr.length > 1 ? 100 / (arr.length - 1) : 100
  return arr.map((p, i) => {
    const x = arr.length > 1 ? i * step : 50
    const y = 33 - (Math.max(0, Number(p.count || 0)) / max) * 30
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
</script>

<style scoped>
.line-chart { display: grid; gap: .45rem; }
.lc-head, .lc-foot {
  display: flex;
  justify-content: space-between;
  color: var(--c-text-4);
  font-size: .74rem;
}
.lc-svg {
  width: 100%;
  height: 140px;
  background: color-mix(in srgb, var(--c-bg-2) 70%, transparent);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
}
.axis {
  stroke: color-mix(in srgb, var(--c-text-4) 40%, transparent);
  stroke-width: .3;
}
.line {
  fill: none;
  stroke: var(--c-brand-h);
  stroke-width: 1.3;
}
.dot { fill: var(--c-accent); }
</style>
