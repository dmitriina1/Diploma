# План редизайна UI — пространство, типографика и структура в стиле OpenAI API

## Область применения
**Только директория `PrimeVue/`** (PrimeVue v4 + Aura preset).  
`frontend-vue/` в этом плане не трогаем.

## Что берём у OpenAI (и что НЕ берём)

| Берём | НЕ берём |
|---|---|
| Вертикальные отступы между секциями | Цветовую палитру |
| Размеры и иерархию заголовков | Замену градиентов на нейтральный чёрный/белый |
| Структуру layout-а (hero, grid, section-heading + subtitle) | Удаление тёмной темы |
| Стиль карточек (blob-градиент, радиус, padding) | Смену PrimeVue Aura на другой preset |
| Pill-форму основных кнопок | Удаление иконок из навигации |
| Чистоту navbar (высота, backdrop-blur) | Анимацию navbar |

---

## Текущая палитра (сохраняем полностью)

```
Тёмная тема: --c-brand #1f8a70  --c-accent #18b4d8  --c-violet #4f7ecf  --c-pop #ff6b35  --c-lime #ccff00
Светлая тема: --c-brand #0f766e  --c-accent #0c91ad  --c-violet #4864e0
```

Blob-градиенты для карточек строим **из этих же токенов**.

---

## Шаг 1 — Типографика (`PrimeVue/src/assets/global.css`)

### Текущие размеры → целевые (OpenAI-scale)

| Класс | Сейчас | Цель |
|---|---|---|
| `.h-display` | `clamp(2rem, 5vw, 3.5rem)` | `clamp(2.8rem, 6vw, 4.5rem)` |
| `.h-page` | `clamp(1.35rem, 2.5vw, 1.95rem)` | `clamp(1.6rem, 3vw, 2.4rem)` |
| `letter-spacing h-display` | `-0.03em` | `-0.04em` |
| `line-height h-display` | `1.12` | `1.08` |
| `html font-size` | `clamp(15px, 0.45vw + 13.2px, 18px)` | оставить |
| `body line-height` | `1.64` | `1.68` |

Добавить новый утилит-класс:
```css
.section-heading {
  font-size: clamp(1.7rem, 3.5vw, 2.6rem);
  font-weight: 740;
  letter-spacing: -0.03em;
  line-height: 1.1;
  color: var(--c-text);
}

.section-lead {
  font-size: 1.05rem;
  color: var(--c-text-3);
  line-height: 1.7;
  max-width: 580px;
}
```

---

## Шаг 2 — Отступы секций (`global.css`)

OpenAI использует ~80–120px вертикального padding на секцию.

Добавить layout-утилиты:
```css
.section          { padding: 80px 0; }
.section-lg       { padding: 112px 0; }
.section-hero     { padding: 96px 0 80px; }
.section-centered { text-align: center; }

.section-header {
  margin-bottom: 3rem;
}
.section-header.centered {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: .75rem;
}
```

Текущий `--max-w: 1320px` и `--max-w-sm: 880px` — оставить.

---

## Шаг 3 — Blob-градиентные карточки (`global.css`)

Новые классы для feature/tool-карточек в стиле OpenAI, но на цветах нашей палитры:

```css
/* Три варианта blob-карточек — чередовать на странице */
.blob-card-1 {
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--c-brand) 55%, transparent) 0%,
    color-mix(in srgb, var(--c-accent) 45%, transparent) 60%,
    color-mix(in srgb, var(--c-violet) 35%, transparent) 100%
  );
  color: #fff;
}

.blob-card-2 {
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--c-violet) 50%, transparent) 0%,
    color-mix(in srgb, var(--c-accent) 50%, transparent) 55%,
    color-mix(in srgb, var(--c-brand) 35%, transparent) 100%
  );
  color: #fff;
}

.blob-card-3 {
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--c-pop) 45%, transparent) 0%,
    color-mix(in srgb, var(--c-brand) 55%, transparent) 60%,
    color-mix(in srgb, var(--c-lime) 30%, transparent) 100%
  );
  color: #fff;
}

/* Базовый класс blob-карточки */
.blob-card {
  border-radius: var(--r-xl);   /* 20px */
  padding: 2rem 2rem 2.5rem;
  border: none;
  box-shadow: var(--shadow-md);
  transition: transform var(--dur) var(--ease-out), box-shadow var(--dur) var(--ease);
  cursor: pointer;
}
.blob-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-lg);
}
.blob-card h3 {
  font-size: 1.2rem;
  font-weight: 680;
  margin-bottom: .5rem;
  letter-spacing: -.01em;
}
.blob-card p {
  font-size: .93rem;
  opacity: .82;
  line-height: 1.55;
}
```

---

## Шаг 4 — PrimeVue Aura — кастомизация токенов (`PrimeVue/src/main.js`)

Расширить конфиг `PrimeVue` через `definePreset`, не меняя `Aura`:

```js
import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

const AppPreset = definePreset(Aura, {
  semantic: {
    borderRadius: {
      sm: '8px',
      md: '12px',    // кнопки, инпуты
      lg: '16px',    // карточки
      xl: '20px',
    },
    primary: {
      // Привязать primary-цвет к нашему --c-brand
      50:  '#e6f7f3',
      100: '#b3e5d8',
      200: '#80d3bd',
      300: '#4dc1a1',
      400: '#29b791',
      500: '#1f8a70',   // --c-brand
      600: '#187a62',
      700: '#116955',
      800: '#0b5847',
      900: '#044739',
    },
  },
  components: {
    button: {
      borderRadius: '9999px',   // pill — как у OpenAI
      paddingX: '1.4rem',
      paddingY: '.65rem',
      fontWeight: '650',
    },
    card: {
      borderRadius: '16px',
      shadow: '0 4px 20px rgba(0,0,0,.15)',
    },
    inputtext: {
      borderRadius: '10px',
    },
    select: {
      borderRadius: '10px',
    },
    dialog: {
      borderRadius: '18px',
    },
    datatable: {
      headerCellBorderRadius: '0',
      rowBorderRadius: '0',
    },
  }
})

app.use(PrimeVue, {
  ripple: true,
  theme: {
    preset: AppPreset,
    options: { darkModeSelector: '[data-theme="dark"]' }
  }
})
```

---

## Шаг 5 — Navbar (`PrimeVue/src/components/NavBar.vue`)

OpenAI navbar: высота 64px, прозрачный/blur фон, тонкая нижняя граница.  
Текущий navbar уже близок по структуре. Изменить только CSS:

```css
.nav {
  height: 64px;           /* было: --nav-h: 76px — обновить переменную */
  padding: 0 2rem;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  /* убрать любые border-bottom с цветным акцентом, заменить на: */
  border-bottom: 1px solid var(--c-border);
  box-shadow: none;
}

.nav-inner {
  height: 100%;
  align-items: center;
}

.nav-link {
  font-size: .92rem;
  font-weight: 500;       /* было 600 — чуть легче, как у OpenAI */
  padding: .35rem .7rem;
  border-radius: var(--r-md);
  transition: background var(--dur) var(--ease), color var(--dur) var(--ease);
}
```

Также обновить `--nav-h: 64px` в `global.css`.

---

## Шаг 6 — Hero-секция (`PrimeVue/src/views/Home.vue`)

OpenAI-паттерн: крупный заголовок, подзаголовок, кнопки CTA, статы — всё с generous padding.

Текущий `Home.vue` уже имеет правильную структуру (2-колоночный hero-grid). Изменения только в CSS:

```css
.hero-grid {
  padding-top: 80px;      /* section-hero spacing */
  padding-bottom: 64px;
  gap: 2rem;
}

.hero-title {
  font-size: clamp(2rem, 4.5vw, 3.4rem);
  letter-spacing: -.03em;
  line-height: 1.1;
  margin-bottom: 1.1rem;
}

.hero-sub {
  font-size: 1.08rem;
  line-height: 1.7;
  color: var(--c-text-2);
  max-width: 520px;
  margin-bottom: 1.8rem;
}

.hero-actions {
  display: flex;
  gap: .9rem;
  flex-wrap: wrap;
  margin-bottom: 2.2rem;
}

/* Статы — без рамок-карточек, как у OpenAI */
.hero-stats {
  display: flex;
  gap: 2.5rem;
  flex-wrap: wrap;
  padding-top: 1.5rem;
  border-top: 1px solid var(--c-border);
}
.hero-stat-value {
  font-size: 2rem;
  font-weight: 780;
  letter-spacing: -.03em;
  color: var(--c-text);
  line-height: 1;
}
.hero-stat-label {
  font-size: .82rem;
  color: var(--c-text-3);
  margin-top: .25rem;
}
```

---

## Шаг 7 — Feature/Tool карточки (`Home.vue`)

Заменить класс `.tool-card` на blob-карточки (из Шага 3). Чередовать `.blob-card-1`, `.blob-card-2`, `.blob-card-3` по индексу:

```vue
<Card
  v-for="(item, i) in features"
  :key="item.route"
  class="blob-card"
  :class="`blob-card-${(i % 3) + 1}`"
  @click="openFeature(item.route)"
>
```

Grid-сетка — сохранить текущую `grid-template-columns: repeat(auto-fit, minmax(260px, 1fr))`.

---

## Шаг 8 — Section-heading паттерн (`Home.vue` и другие страницы)

Применить по всему сайту единый паттерн заголовка секции:

```vue
<div class="section-header centered">
  <h2 class="section-heading">Заголовок секции</h2>
  <p class="section-lead">Краткое описание ценности</p>
</div>
```

Страницы для обновления: `Home.vue`, `InterviewQuestions.vue`, `HHRequirements.vue`, `TestAssignments.vue`.

---

## Шаг 9 — Footer (`PrimeVue/src/components/AppFooter.vue`)

OpenAI footer: `background: var(--c-bg-2)`, `border-top: 1px solid var(--c-border)`, многоколоночная сетка, мелкий шрифт.

Обновить только CSS — структура уже многоколоночная. Убрать тёмный контрастный фон (если есть), заменить на `--c-bg-2`.

---

## Порядок реализации

1. `global.css` — типографика, spacing-утилиты, blob-card классы, `--nav-h: 64px`
2. `main.js` — `definePreset` с pill-кнопками, border-radius токенами, primary цветом
3. `NavBar.vue` — высота 64px, чистый border-bottom
4. `Home.vue` — hero spacing, blob-карточки, section-heading паттерн
5. `AppFooter.vue` — фон на `--c-bg-2`
6. Остальные страницы — добавить `.section`, `.section-heading`, `.section-lead`

---

## Что НЕ трогаем

- Цветовые токены (`--c-bg`, `--c-brand`, `--c-accent` и все остальные)
- Логику и `<script>` компонентов
- Структуру роутера и store
- Фоновые градиенты `body`
- Тёмную/светлую тему
- Директорию `frontend-vue/`
