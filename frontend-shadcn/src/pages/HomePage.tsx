import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowRight,
  BookOpen,
  Brain,
  Sparkles,
  Bot,
  Video,
  Trophy,
  TrendingUp,
  Search,
  Mic2,
  PlayCircle,
  CheckCircle2,
  Clock,
  Users,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { GridPattern } from '@/components/effects/grid-pattern'
import { DotPattern } from '@/components/effects/dot-pattern'
import { Spotlight } from '@/components/effects/spotlight'
import { AnimatedShinyText } from '@/components/effects/animated-shiny-text'
import { BorderBeam } from '@/components/effects/border-beam'
import { questionsApi } from '@/api'
import { cn } from '@/lib/utils'
import type { PublicStats } from '@/types'

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
}

const features = [
  {
    icon: Video,
    title: 'Анализ видео',
    description: 'YouTube, VK, Rutube, OK.ru, Dailymotion, Vimeo. yt-dlp + Whisper large-v3.',
    accent: 'from-violet-500 to-fuchsia-500',
  },
  {
    icon: Brain,
    title: 'Извлечение вопросов',
    description: 'LLM (GPT-4o / Gemini / Llama-3.1) автоматически структурирует Q&A.',
    accent: 'from-cyan-500 to-blue-500',
  },
  {
    icon: Sparkles,
    title: 'Умный поиск',
    description: 'FAISS-эмбеддинги для семантического поиска похожих вопросов.',
    accent: 'from-emerald-500 to-cyan-500',
  },
  {
    icon: Bot,
    title: 'AI-интервью',
    description: 'Чатбот, который проводит собеседование и даёт обратную связь.',
    accent: 'from-amber-500 to-rose-500',
  },
  {
    icon: Trophy,
    title: 'SM-2 тренажёр',
    description: 'Интервальное повторение с 3D-флипкартами и keyboard shortcuts.',
    accent: 'from-rose-500 to-violet-500',
  },
  {
    icon: TrendingUp,
    title: 'HH-аналитика',
    description: '214+ навыков из вакансий с фильтрами и графиками.',
    accent: 'from-sky-500 to-emerald-500',
  },
]

const pipelineSteps = [
  { step: '01', title: 'Видео URL', text: 'Вставьте ссылку с YouTube/VK/Rutube' },
  { step: '02', title: 'Транскрибация', text: 'faster-whisper large-v3-turbo' },
  { step: '03', title: 'Извлечение', text: 'LLM находит Q&A' },
  { step: '04', title: 'Структуризация', text: 'PostgreSQL + теги + дедуп' },
  { step: '05', title: 'Подготовка', text: 'SM-2 / mock / AI-чат' },
]

const professions = [
  'Frontend',
  'Backend',
  'DevOps',
  'Data Engineer',
  'ML Engineer',
  'QA',
  'Mobile (iOS/Android)',
  'Game Dev',
  'Embedded',
  'Cloud',
  'SRE',
  'Security',
]

export function HomePage() {
  const [stats, setStats] = useState<PublicStats | null>(null)

  useEffect(() => {
    questionsApi
      .publicStats()
      .then((r) => setStats(r.data as PublicStats))
      .catch(() => undefined)
  }, [])

  return (
    <div className="relative">
      {/* HERO */}
      <section className="relative isolate overflow-hidden">
        <GridPattern
          width={36}
          height={36}
          className="[mask-image:radial-gradient(800px_circle_at_top,white,transparent)] -z-10"
          strokeDasharray="2 2"
        />
        <Spotlight
          className="-top-40 left-0 md:-top-20 md:left-60"
          fill="oklch(0.7 0.22 286)"
        />

        <div className="mx-auto max-w-7xl px-4 pt-16 pb-20 sm:px-6 sm:pt-24 sm:pb-28">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="mx-auto flex max-w-3xl flex-col items-center text-center"
          >
            <Link
              to="/recordings"
              className="group mb-6 inline-flex items-center gap-2 rounded-full border border-border/60 bg-card/50 px-4 py-1.5 text-xs backdrop-blur-md hover:border-primary/30"
            >
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-primary" />
              </span>
              <AnimatedShinyText className="!mx-0 inline-flex items-center justify-center text-xs">
                Новый пайплайн обработки видео уже в работе
              </AnimatedShinyText>
              <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
            </Link>

            <h1 className="text-balance bg-gradient-to-br from-foreground from-30% via-foreground/90 to-foreground/40 bg-clip-text text-4xl font-bold leading-[1.05] tracking-tight text-transparent sm:text-6xl md:text-7xl">
              Готовьтесь к IT-собеседованиям{' '}
              <span className="gradient-text">структурно</span>
            </h1>

            <p className="mt-6 max-w-2xl text-balance text-base text-muted-foreground sm:text-lg">
              InterviewHub извлекает вопросы из видео-интервью с помощью Whisper и LLM, систематизирует
              их в единую базу и помогает закрепить ответы через SM-2, mock-собеседования и AI-чат.
            </p>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Button asChild size="lg" variant="gradient" className="rounded-full">
                <Link to="/interview-questions">
                  Начать подготовку <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="rounded-full">
                <Link to="/trainer">
                  <Trophy className="h-4 w-4" /> Открыть тренажёр
                </Link>
              </Button>
            </div>

            {/* Stats strip */}
            <div className="mt-12 grid w-full grid-cols-2 gap-2 sm:grid-cols-4 sm:gap-4">
              <StatTile label="Вопросов" value={stats?.questions_count ?? '10K+'} icon={BookOpen} />
              <StatTile label="Видео" value={stats?.videos_count ?? '630+'} icon={Video} />
              <StatTile label="Профессий" value={stats?.professions_count ?? '26'} icon={Users} />
              <StatTile label="Заданий" value={stats?.test_assignments_count ?? '50+'} icon={CheckCircle2} />
            </div>
          </motion.div>
        </div>
      </section>

      {/* TICKER */}
      <section className="border-y border-border/60 bg-card/30 py-6">
        <p className="mb-3 text-center text-xs uppercase tracking-widest text-muted-foreground">
          Поддерживаемые направления подготовки
        </p>
        <div className="relative flex overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_10%,black_90%,transparent)]">
          <div className="flex shrink-0 animate-marquee gap-8 px-4 will-change-transform">
            {[...professions, ...professions].map((p, i) => (
              <span
                key={`${p}-${i}`}
                className="inline-flex h-8 items-center rounded-full border border-border/60 bg-background/40 px-4 text-sm text-muted-foreground"
              >
                {p}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <Badge variant="outline" className="mb-3">
            Возможности платформы
          </Badge>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Не просто список вопросов
          </h2>
          <p className="mt-3 text-muted-foreground">
            Цикл: <strong>извлечение → структуризация → повторение → проверка</strong>. Каждый этап
            автоматизирован и работает в едином стеке.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f, idx) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.4, delay: idx * 0.05 }}
            >
              <Card className="group relative h-full overflow-hidden transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/10">
                <div className={cn('absolute inset-x-0 top-0 h-px bg-gradient-to-r opacity-0 transition-opacity group-hover:opacity-100', f.accent)} />
                <CardContent className="flex h-full flex-col gap-3 p-6">
                  <div className={cn('inline-flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-md', f.accent)}>
                    <f.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-semibold tracking-tight">{f.title}</h3>
                  <p className="text-sm text-muted-foreground">{f.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* PIPELINE */}
      <section className="relative mx-auto max-w-7xl px-4 pb-20 sm:px-6 sm:pb-28">
        <Card className="relative overflow-hidden">
          <DotPattern className="[mask-image:radial-gradient(400px_circle_at_center,white,transparent)] opacity-50" />
          <BorderBeam size={250} duration={12} />
          <CardContent className="relative grid gap-10 p-8 sm:p-12 lg:grid-cols-2">
            <div className="flex flex-col justify-center">
              <Badge variant="gradient" className="w-fit">
                Pipeline
              </Badge>
              <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
                Видео → база знаний за 5 шагов
              </h2>
              <p className="mt-3 text-muted-foreground">
                Без ручной разметки. Whisper + LLM делают всю работу. Вы получаете
                готовый каталог вопросов с тегами, оценкой вероятности и привязкой
                к видео-таймингу.
              </p>
              <div className="mt-6 flex gap-3">
                <Button asChild variant="default">
                  <Link to="/suggest">
                    <PlayCircle className="h-4 w-4" /> Предложить видео
                  </Link>
                </Button>
                <Button asChild variant="ghost">
                  <Link to="/recordings">Все записи</Link>
                </Button>
              </div>
            </div>
            <ol className="relative flex flex-col gap-3">
              {pipelineSteps.map((s, idx) => (
                <motion.li
                  key={s.step}
                  initial={{ opacity: 0, x: 12 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.05 }}
                  className="group relative flex gap-4 rounded-xl border border-border/60 bg-background/50 p-4 backdrop-blur-sm transition-colors hover:border-primary/30"
                >
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 font-mono text-xs font-semibold text-primary">
                    {s.step}
                  </span>
                  <div>
                    <p className="font-semibold">{s.title}</p>
                    <p className="text-sm text-muted-foreground">{s.text}</p>
                  </div>
                </motion.li>
              ))}
            </ol>
          </CardContent>
        </Card>
      </section>

      {/* CTA grid */}
      <section className="mx-auto max-w-7xl px-4 pb-24 sm:px-6">
        <div className="grid gap-4 lg:grid-cols-3">
          <CtaCard
            to="/interview-questions"
            icon={Search}
            title="Каталог вопросов"
            description="Полная база с фильтрами по технологиям и уровням."
          />
          <CtaCard
            to="/ai-interview"
            icon={Bot}
            title="AI Interview"
            description="Чат-бот проведёт собеседование и оценит ваши ответы."
          />
          <CtaCard
            to="/mock-interview"
            icon={Mic2}
            title="Mock-сессии"
            description="Реалистичные симуляции с разбором результатов."
          />
        </div>
      </section>
    </div>
  )
}

function StatTile({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: string | number
  icon: React.ComponentType<{ className?: string }>
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border/60 bg-card/40 px-4 py-3 backdrop-blur-sm">
      <Icon className="h-5 w-5 text-primary" />
      <div className="flex flex-col text-left">
        <span className="text-xl font-bold leading-none">{value}</span>
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
    </div>
  )
}

function CtaCard({
  to,
  icon: Icon,
  title,
  description,
}: {
  to: string
  icon: React.ComponentType<{ className?: string }>
  title: string
  description: string
}) {
  return (
    <Link to={to}>
      <Card className="group relative h-full overflow-hidden transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/10">
        <CardContent className="flex flex-col gap-3 p-6">
          <Icon className="h-6 w-6 text-primary" />
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
          <span className="mt-2 inline-flex items-center gap-1 text-sm text-primary">
            Открыть <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </span>
        </CardContent>
      </Card>
    </Link>
  )
}

// Used to silence unused import warnings — keeps icons referenced in case of future re-use.
export const _icons = { Clock }
