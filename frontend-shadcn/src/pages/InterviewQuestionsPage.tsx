import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowRight, BookOpen, ChevronLeft, ChevronRight, Loader2, Search, Sparkles, X } from 'lucide-react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { PageHeader } from '@/components/layout/page-header'
import { questionsApi } from '@/api'
import { cn, truncate } from '@/lib/utils'
import type { Question } from '@/types'

const difficulties = [
  { v: 'all', l: 'Любая сложность' },
  { v: 'junior', l: 'Junior' },
  { v: 'middle', l: 'Middle' },
  { v: 'senior', l: 'Senior' },
]

const sorts = [
  { v: 'probability', l: 'По вероятности' },
  { v: 'date', l: 'По дате' },
  { v: 'alpha', l: 'По алфавиту' },
]

const PER_PAGE = 20

export function InterviewQuestionsPage() {
  const [params, setParams] = useSearchParams()
  const profession = params.get('profession') || ''
  const [questions, setQuestions] = useState<Question[]>([])
  const [tags, setTags] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const search = params.get('q') || ''
  const tech = params.get('tech') || 'all'
  const diff = params.get('diff') || 'all'
  const sort = params.get('sort') || 'probability'
  const page = Math.max(1, parseInt(params.get('page') || '1', 10))

  const setParam = (k: string, v: string | null) => {
    const next = new URLSearchParams(params)
    if (!v || v === 'all') next.delete(k)
    else next.set(k, v)
    if (k !== 'page') next.delete('page')
    setParams(next, { replace: true })
  }

  useEffect(() => {
    setLoading(true)
    setError(null)
    const fetcher = profession
      ? questionsApi.professionQuestions(profession, { limit: 1000 })
      : questionsApi.list({ limit: 1000 })
    fetcher
      .then((r) => {
        const data = r.data
        const items = (Array.isArray(data) ? data : data.items || data.questions || []) as Question[]
        setQuestions(items)
      })
      .catch(() => setError('Не удалось загрузить вопросы. Попробуйте позже.'))
      .finally(() => setLoading(false))

    questionsApi.tags().then((r) => {
      const data = r.data
      const list = Array.isArray(data) ? data : data.items || []
      setTags(list.map((t: { name?: string } | string) => (typeof t === 'string' ? t : t.name || '')).filter(Boolean))
    }).catch(() => undefined)
  }, [profession])

  const filtered = useMemo(() => {
    const lower = search.trim().toLowerCase()
    let arr = questions.filter((q) => {
      if (lower && !q.text?.toLowerCase().includes(lower) && !(q.answer || '').toLowerCase().includes(lower)) return false
      if (tech !== 'all' && q.technology !== tech && !(q.tags || []).includes(tech)) return false
      if (diff !== 'all') {
        const d = q.difficulty
        const lbl = typeof d === 'number' ? (d <= 1 ? 'junior' : d <= 2 ? 'middle' : 'senior') : (d as unknown as string)
        if (lbl !== diff) return false
      }
      return true
    })
    arr = [...arr]
    if (sort === 'probability') arr.sort((a, b) => (b.probability || 0) - (a.probability || 0))
    else if (sort === 'date') arr.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
    else if (sort === 'alpha') arr.sort((a, b) => (a.text || '').localeCompare(b.text || ''))
    return arr
  }, [questions, search, tech, diff, sort])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE))
  const safePage = Math.min(page, totalPages)
  const sliced = filtered.slice((safePage - 1) * PER_PAGE, safePage * PER_PAGE)

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <PageHeader
        icon={<BookOpen className="h-5 w-5" />}
        title={profession ? `Вопросы: ${profession}` : 'Каталог вопросов'}
        description="Реальные вопросы с IT-собеседований, извлечённые из видео и проверенные модераторами"
        actions={profession ? (
          <Button variant="outline" size="sm" onClick={() => setParam('profession', null)}>
            <X className="h-4 w-4" /> Сбросить профессию
          </Button>
        ) : undefined}
      />

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setParam('q', e.target.value)}
              placeholder="Поиск по вопросу или ответу…"
              className="pl-9"
            />
          </div>
          <Select value={tech} onValueChange={(v) => setParam('tech', v)}>
            <SelectTrigger className="w-full sm:w-44">
              <SelectValue placeholder="Технология" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все технологии</SelectItem>
              {tags.slice(0, 100).map((t) => (
                <SelectItem key={t} value={t}>{t}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={diff} onValueChange={(v) => setParam('diff', v)}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Сложность" />
            </SelectTrigger>
            <SelectContent>
              {difficulties.map((d) => (
                <SelectItem key={d.v} value={d.v}>{d.l}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={sort} onValueChange={(v) => setParam('sort', v)}>
            <SelectTrigger className="w-full sm:w-44">
              <SelectValue placeholder="Сортировка" />
            </SelectTrigger>
            <SelectContent>
              {sorts.map((s) => (
                <SelectItem key={s.v} value={s.v}>{s.l}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <div className="mb-3 flex items-center justify-between text-sm text-muted-foreground">
        <span>{loading ? 'Загрузка…' : `Найдено: ${filtered.length}`}</span>
        {!loading && totalPages > 1 && (
          <span>Страница {safePage} из {totalPages}</span>
        )}
      </div>

      {error && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardContent className="p-6 text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      {loading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <Sparkles className="h-8 w-8 text-muted-foreground" />
            <p className="text-base font-semibold">Вопросы не найдены</p>
            <p className="text-sm text-muted-foreground">Попробуйте изменить фильтры или поиск</p>
          </CardContent>
        </Card>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="flex flex-col gap-2">
          {sliced.map((q, idx) => (
            <motion.div
              key={q.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: Math.min(idx * 0.02, 0.3) }}
            >
              <Link to={`/question/${q.id}`} className="block">
                <Card className="group transition-all hover:-translate-y-px hover:border-primary/30 hover:shadow-md">
                  <CardContent className="flex items-center gap-3 p-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium leading-snug sm:text-base">{q.text}</p>
                      {q.answer && (
                        <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">{truncate(q.answer.replace(/\s+/g, ' '), 160)}</p>
                      )}
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        {q.technology && <Badge variant="info">{q.technology}</Badge>}
                        {(q.tags || []).slice(0, 3).map((t) => (
                          <Badge key={t} variant="secondary">{t}</Badge>
                        ))}
                        {q.difficulty != null && (
                          <Badge variant={diffVariant(q.difficulty)}>{diffLabel(q.difficulty)}</Badge>
                        )}
                        {q.probability != null && (
                          <span className="text-xs text-muted-foreground">
                            {(q.probability * (q.probability < 1 ? 100 : 1)).toFixed(0)}% вероятность
                          </span>
                        )}
                      </div>
                    </div>
                    <ArrowRight className="hidden h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary sm:block" />
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      )}

      {!loading && totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="icon"
            disabled={safePage <= 1}
            onClick={() => setParam('page', String(safePage - 1))}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="px-3 text-sm font-medium">{safePage} / {totalPages}</span>
          <Button
            variant="outline"
            size="icon"
            disabled={safePage >= totalPages}
            onClick={() => setParam('page', String(safePage + 1))}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}

function diffLabel(d: number | string | null | undefined): string {
  if (d == null) return ''
  if (typeof d === 'string') return d
  if (d <= 1) return 'Junior'
  if (d <= 2) return 'Middle'
  return 'Senior'
}

function diffVariant(d: number | string | null | undefined): 'success' | 'warning' | 'destructive' | 'secondary' {
  const lbl = (typeof d === 'string' ? d : diffLabel(d)).toLowerCase()
  if (lbl.includes('junior')) return 'success'
  if (lbl.includes('middle')) return 'warning'
  if (lbl.includes('senior')) return 'destructive'
  return 'secondary'
}

// referenced to silence unused import warning
export const _loaderIcon = Loader2
export const _cn = cn
