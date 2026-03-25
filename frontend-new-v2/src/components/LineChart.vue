<template>
  <div class="line-chart">
    <div v-if="plotted.length" class="lc-metrics">
      <span>Пик: <b>{{ maxValue }}</b> {{ unit }}</span>
      <span>Среднее: <b>{{ avgValue }}</b> {{ unit }}</span>
      <span>Последнее: <b>{{ lastValue }}</b> {{ unit }}</span>
    </div>
    <div class="lc-captions">
      <span>Ось Y: {{ yLabel }} ({{ unit }})</span>
      <span>Ось X: {{ xLabel }}</span>
    </div>
    <div class="lc-legend">
      <span class="legend-item">
        <span class="legend-swatch line-swatch"></span>
        Тренд
      </span>
      <button class="legend-toggle" @click="showAverageLine = !showAverageLine" type="button">
        <span class="legend-swatch avg-swatch" :class="{ muted: !showAverageLine }"></span>
        {{ showAverageLine ? 'Средняя линия: вкл' : 'Средняя линия: выкл' }}
      </button>
    </div>
    <div class="lc-plot-wrap">
      <svg viewBox="0 0 100 42" preserveAspectRatio="none" class="lc-svg" aria-label="line-chart">
      <defs>
        <linearGradient :id="gradientId" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="var(--c-brand-h)" stop-opacity="0.32" />
          <stop offset="100%" stop-color="var(--c-brand-h)" stop-opacity="0" />
        </linearGradient>
      </defs>
      <line v-for="y in gridLines" :key="`grid-${y}`" x1="10" :y1="y" x2="98" :y2="y" class="grid" />
      <line x1="10" y1="4" x2="10" y2="36" class="axis" />
      <line x1="10" y1="36" x2="98" y2="36" class="axis" />
      <line v-if="plotted.length && showAverageLine" x1="10" :y1="avgY" x2="98" :y2="avgY" class="avg-line" />
      <polygon v-if="areaPoints" :points="areaPoints" class="area" :style="{ fill: `url(#${gradientId})` }" />
      <polyline :points="polylinePoints" class="line" />
      <g
        v-for="p in plotted"
        :key="p.key"
        class="dot-group"
        @mouseenter="showTooltip(p)"
        @mousemove="showTooltip(p)"
        @mouseleave="hideTooltip"
      >
        <circle :cx="p.x" :cy="p.y" r="1.1" class="dot-hit" />
        <circle :cx="p.x" :cy="p.y" r="0.8" class="dot" />
      </g>
      </svg>
      <div
        v-if="tooltip.visible"
        class="lc-tooltip"
        :class="{ left: tooltip.alignLeft, below: tooltip.placeBelow }"
        :style="{ left: `${tooltip.cx}%`, top: `${(tooltip.cy / 42) * 100}%` }"
      >
        {{ tooltip.text }}
      </div>
    </div>
    <div class="lc-scale">
      <span>{{ maxValue }} {{ unit }}</span>
      <span>{{ midValue }} {{ unit }}</span>
      <span>0 {{ unit }}</span>
    </div>
    <div class="lc-foot" v-if="plotted.length">
      <span>{{ plotted[0].labelShort }}</span>
      <span>{{ plotted[middleIndex]?.labelShort || plotted[0].labelShort }}</span>
      <span>{{ plotted[plotted.length - 1].labelShort }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  points: { type: Array, default: () => [] },
  unit: { type: String, default: 'шт' },
  tooltipUnit: { type: String, default: '' },
  xLabel: { type: String, default: 'Дата' },
  yLabel: { type: String, default: 'Значение' }
})

const showAverageLine = ref(true)

const maxValue = computed(() => Math.max(...props.points.map((p) => Number(p.count || 0)), 1))
const midValue = computed(() => Math.round(maxValue.value / 2))
const gridLines = [4, 12, 20, 28, 36]
const gradientId = `lc-grad-${Math.random().toString(36).slice(2, 9)}`

const formatLabel = (day) => {
  if (!day) return '-'
  if (/^\d{4}-\d{2}-\d{2}$/.test(day)) return `${day.slice(8, 10)}.${day.slice(5, 7)}`
  return day
}

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
      labelShort: formatLabel(p.day),
      value: Number(p.count || 0)
    }
  })
})

const polylinePoints = computed(() => plotted.value.map((p) => `${p.x},${p.y}`).join(' '))
const middleIndex = computed(() => Math.floor((plotted.value.length - 1) / 2))
const areaPoints = computed(() => {
  if (!plotted.value.length) return ''
  const first = plotted.value[0]
  const last = plotted.value[plotted.value.length - 1]
  return `${first.x},36 ${plotted.value.map((p) => `${p.x},${p.y}`).join(' ')} ${last.x},36`
})
const avgRaw = computed(() => {
  if (!props.points.length) return 0
  const sum = props.points.reduce((acc, p) => acc + Number(p.count || 0), 0)
  return sum / props.points.length
})
const avgValue = computed(() => Math.round(avgRaw.value))
const avgY = computed(() => 36 - (Math.max(0, avgRaw.value) / maxValue.value) * 32)
const lastValue = computed(() => {
  if (!props.points.length) return 0
  return Math.round(Number(props.points[props.points.length - 1]?.count || 0))
})
const tooltipUnitLabel = computed(() => props.tooltipUnit || props.unit)

const tooltip = ref({
  visible: false,
  text: '',
  cx: 0,
  cy: 0,
  alignLeft: false,
  placeBelow: false
})

const showTooltip = (p) => {
  const text = `${p.labelShort} — ${p.value} ${tooltipUnitLabel.value}`
  tooltip.value = {
    visible: true,
    text,
    cx: p.x,
    cy: p.y,
    alignLeft: p.x > 80,
    placeBelow: p.y < 12
  }
}

const hideTooltip = () => {
  tooltip.value.visible = false
}
</script>

<style scoped>
.line-chart { display: grid; gap: .45rem; }
.lc-metrics {
  display: flex;
  justify-content: space-between;
  gap: .75rem;
  flex-wrap: wrap;
  font-size: .76rem;
  color: var(--c-text-3);
}
.lc-metrics b { color: var(--c-text); font-weight: 700; }
.lc-captions, .lc-scale, .lc-foot {
  display: flex;
  justify-content: space-between;
  color: var(--c-text-4);
  font-size: .74rem;
}
.lc-legend {
  display: flex;
  align-items: center;
  gap: .75rem;
  flex-wrap: wrap;
  font-size: .74rem;
  color: var(--c-text-3);
}
.legend-item,
.legend-toggle {
  display: inline-flex;
  align-items: center;
  gap: .35rem;
}
.legend-toggle {
  border: 1px solid var(--c-border);
  background: var(--c-bg-2);
  color: var(--c-text-3);
  border-radius: var(--r-sm);
  padding: .2rem .45rem;
  cursor: pointer;
}
.legend-toggle:hover {
  color: var(--c-text-2);
  border-color: color-mix(in srgb, var(--c-brand) 36%, var(--c-border));
}
.legend-swatch {
  width: 15px;
  height: 0;
  border-top: 2px solid var(--c-brand-h);
  border-radius: 2px;
}
.line-swatch { border-top-color: var(--c-brand-h); }
.avg-swatch {
  border-top-color: color-mix(in srgb, var(--c-accent) 70%, transparent);
  border-top-style: dashed;
}
.avg-swatch.muted { border-top-color: color-mix(in srgb, var(--c-text-4) 45%, transparent); }
.lc-scale { font-variant-numeric: tabular-nums; }
.lc-plot-wrap { position: relative; }
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
.avg-line {
  stroke: color-mix(in srgb, var(--c-accent) 70%, transparent);
  stroke-width: .26;
  stroke-dasharray: 1.2 1.2;
}
.area { pointer-events: none; }
.axis {
  stroke: color-mix(in srgb, var(--c-text-4) 40%, transparent);
  stroke-width: .3;
}
.line {
  fill: none;
  stroke: var(--c-brand-h);
  stroke-width: 1.65;
}
.dot-group { cursor: crosshair; }
.dot-hit { fill: transparent; }
.dot { fill: var(--c-accent); transition: r .12s ease; }
.dot-group:hover .dot { r: 1.05; }
.lc-tooltip {
  position: absolute;
  z-index: 5;
  max-width: calc(100% - 12px);
  pointer-events: none;
  white-space: nowrap;
  font-size: .76rem;
  font-weight: 600;
  color: var(--c-text);
  background: color-mix(in srgb, var(--c-bg) 92%, var(--c-surface));
  border: 1px solid color-mix(in srgb, var(--c-border) 74%, transparent);
  border-radius: var(--r-sm);
  padding: .22rem .45rem;
  transform: translate(10px, calc(-100% - 10px));
  box-shadow: 0 8px 22px rgba(0, 0, 0, .14);
}
.lc-tooltip.left { transform: translate(calc(-100% - 10px), calc(-100% - 10px)); }
.lc-tooltip.below { transform: translate(10px, 10px); }
.lc-tooltip.left.below { transform: translate(calc(-100% - 10px), 10px); }
</style>
