import { useEffect, useState } from 'react'
import {
  Shield,
  Loader2,
  CheckCircle2,
  XCircle,
  Wand2,
  Trash2,
  Calculator,
  RefreshCw,
  Download,
  Send,
} from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PageHeader } from '@/components/layout/page-header'
import { adminApi } from '@/api'
import type { AdminStats, Feedback, Question, Suggestion } from '@/types'
import { formatDateTime } from '@/lib/utils'

export function AdminPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <PageHeader
        icon={<Shield className="h-5 w-5" />}
        title="Админ-панель"
        description="Модерация контента, аналитика, управление интеграциями"
      />

      <Tabs defaultValue="stats" className="w-full">
        <TabsList className="grid w-full grid-cols-3 sm:grid-cols-6">
          <TabsTrigger value="stats">Статистика</TabsTrigger>
          <TabsTrigger value="questions">Вопросы</TabsTrigger>
          <TabsTrigger value="suggestions">Идеи</TabsTrigger>
          <TabsTrigger value="feedback">Отзывы</TabsTrigger>
          <TabsTrigger value="videos">Видео</TabsTrigger>
          <TabsTrigger value="hh">HH</TabsTrigger>
        </TabsList>
        <TabsContent value="stats" className="mt-6"><StatsTab /></TabsContent>
        <TabsContent value="questions" className="mt-6"><QuestionsTab /></TabsContent>
        <TabsContent value="suggestions" className="mt-6"><SuggestionsTab /></TabsContent>
        <TabsContent value="feedback" className="mt-6"><FeedbackTab /></TabsContent>
        <TabsContent value="videos" className="mt-6"><VideosTab /></TabsContent>
        <TabsContent value="hh" className="mt-6"><HHTab /></TabsContent>
      </Tabs>
    </div>
  )
}

function StatsTab() {
  const [stats, setStats] = useState<AdminStats | null>(null)
  useEffect(() => { adminApi.getStats().then((r) => setStats(r.data)).catch(() => undefined) }, [])
  const items: Array<{ key: keyof AdminStats; label: string; accent: string }> = [
    { key: 'questions_total', label: 'Всего вопросов', accent: 'from-violet-500 to-fuchsia-500' },
    { key: 'questions_pending', label: 'На модерации', accent: 'from-amber-500 to-rose-500' },
    { key: 'questions_approved', label: 'Одобрено', accent: 'from-emerald-500 to-cyan-500' },
    { key: 'videos_total', label: 'Видео в базе', accent: 'from-blue-500 to-cyan-500' },
    { key: 'feedback_total', label: 'Отзывов', accent: 'from-rose-500 to-violet-500' },
    { key: 'suggestions_pending', label: 'Идей в очереди', accent: 'from-cyan-500 to-emerald-500' },
  ]
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((it, idx) => (
        <motion.div key={String(it.key)} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.04 }}>
          <Card className="overflow-hidden">
            <CardContent className="p-5">
              <p className="text-xs uppercase tracking-wider text-muted-foreground">{it.label}</p>
              <p className={`mt-2 bg-gradient-to-r ${it.accent} bg-clip-text text-3xl font-bold text-transparent`}>
                {(stats?.[it.key] as number | undefined) ?? '—'}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  )
}

function QuestionsTab() {
  const [items, setItems] = useState<Question[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved'>('pending')
  const [search, setSearch] = useState('')

  function load() {
    setLoading(true)
    adminApi.getQuestions({
      status: filter === 'all' ? undefined : filter,
      search: search || undefined,
      limit: 100,
    })
      .then((r) => {
        const data = r.data
        setItems((Array.isArray(data) ? data : data.items || []) as Question[])
      })
      .finally(() => setLoading(false))
  }
  useEffect(load, [filter, search])

  async function approve(id: number) {
    await adminApi.approve([id])
    toast.success('Одобрено')
    load()
  }
  async function revoke(id: number) {
    await adminApi.revoke([id])
    toast.success('Отозвано')
    load()
  }
  async function generateAnswer(id: number) {
    try {
      await adminApi.generateAnswer(id)
      toast.success('Ответ сгенерирован')
      load()
    } catch { toast.error('Ошибка генерации') }
  }
  async function remove(id: number) {
    if (!confirm('Удалить вопрос?')) return
    await adminApi.deleteQuestion(id)
    toast.success('Удалено')
    load()
  }
  async function recalc() {
    try {
      await adminApi.recalcProbabilities()
      toast.success('Пересчёт запущен')
    } catch { toast.error('Ошибка') }
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {(['all', 'pending', 'approved'] as const).map((f) => (
            <Button key={f} size="sm" variant={filter === f ? 'default' : 'outline'} onClick={() => setFilter(f)}>
              {f === 'all' ? 'Все' : f === 'pending' ? 'Ожидают' : 'Одобренные'}
            </Button>
          ))}
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск…"
            className="ml-auto h-8 max-w-xs"
          />
          <Button size="sm" variant="ghost" onClick={recalc}>
            <Calculator className="h-4 w-4" /> Пересчёт вероятностей
          </Button>
        </div>
        {loading ? (
          <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : (
          <div className="flex flex-col gap-2">
            {items.map((q) => (
              <div key={q.id} className="flex items-start gap-3 rounded-lg border border-border/50 p-3">
                <div className="flex-1">
                  <p className="text-sm font-medium">{q.text}</p>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {q.is_approved ? <Badge variant="success">approved</Badge> : <Badge variant="warning">pending</Badge>}
                    {q.technology && <Badge variant="info">{q.technology}</Badge>}
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button size="icon" variant="ghost" onClick={() => generateAnswer(q.id)} title="Сгенерировать ответ">
                    <Wand2 className="h-4 w-4" />
                  </Button>
                  {!q.is_approved ? (
                    <Button size="icon" variant="ghost" onClick={() => approve(q.id)} title="Одобрить">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    </Button>
                  ) : (
                    <Button size="icon" variant="ghost" onClick={() => revoke(q.id)} title="Отозвать">
                      <XCircle className="h-4 w-4 text-amber-500" />
                    </Button>
                  )}
                  <Button size="icon" variant="ghost" onClick={() => remove(q.id)} title="Удалить">
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            ))}
            {!items.length && <p className="py-6 text-center text-sm text-muted-foreground">Пусто</p>}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function SuggestionsTab() {
  const [items, setItems] = useState<Suggestion[]>([])
  const [loading, setLoading] = useState(true)
  function load() {
    setLoading(true)
    adminApi.getSuggestions()
      .then((r) => {
        const data = r.data
        setItems((Array.isArray(data) ? data : data.items || []) as Suggestion[])
      })
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  async function approve(id: number) {
    await adminApi.updateSuggestion(id, { status: 'approved' })
    toast.success('Одобрено')
    load()
  }
  async function reject(id: number) {
    await adminApi.updateSuggestion(id, { status: 'rejected' })
    load()
  }
  async function process(id: number) {
    try {
      await adminApi.processSuggestion(id)
      toast.success('Запущена обработка')
      load()
    } catch { toast.error('Ошибка') }
  }

  return (
    <Card>
      <CardContent className="p-4">
        {loading ? (
          <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : (
          <div className="flex flex-col gap-2">
            {items.map((s) => (
              <div key={s.id} className="rounded-lg border border-border/50 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={statusVariant(s.status)}>{s.status}</Badge>
                  <a href={s.url} target="_blank" rel="noreferrer" className="text-sm font-medium hover:underline truncate">
                    {s.url}
                  </a>
                  <span className="ml-auto text-xs text-muted-foreground">{s.created_at && formatDateTime(s.created_at)}</span>
                </div>
                {s.description && <p className="mt-1 text-sm text-muted-foreground">{s.description}</p>}
                <div className="mt-2 flex gap-1">
                  <Button size="sm" variant="outline" onClick={() => approve(s.id)}>Одобрить</Button>
                  <Button size="sm" variant="ghost" onClick={() => reject(s.id)}>Отклонить</Button>
                  <Button size="sm" variant="default" onClick={() => process(s.id)}>
                    <Send className="h-3.5 w-3.5" /> Обработать
                  </Button>
                </div>
              </div>
            ))}
            {!items.length && <p className="py-6 text-center text-sm text-muted-foreground">Идей нет</p>}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function FeedbackTab() {
  const [items, setItems] = useState<Feedback[]>([])
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    adminApi.getFeedback({ limit: 100 })
      .then((r) => {
        const data = r.data
        setItems((Array.isArray(data) ? data : data.items || []) as Feedback[])
      })
      .finally(() => setLoading(false))
  }, [])
  return (
    <Card>
      <CardContent className="p-4">
        {loading ? <Loader2 className="mx-auto h-6 w-6 animate-spin" /> : (
          <div className="flex flex-col gap-2">
            {items.map((f) => (
              <div key={f.id} className="rounded-lg border border-border/50 p-3">
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-[10px]">{f.status || 'new'}</Badge>
                  <span className="text-xs text-muted-foreground">{formatDateTime(f.created_at || '')}</span>
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm">{f.message}</p>
                {f.page && <p className="mt-1 text-xs text-muted-foreground">Стр.: {f.page}</p>}
              </div>
            ))}
            {!items.length && <p className="py-6 text-center text-sm text-muted-foreground">Отзывов нет</p>}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

interface VideoEntry {
  id: number
  title: string
  url: string
  platform?: string
  channel?: string | null
  thumbnail_url?: string | null
  questions_count?: number
  created_at?: string
}

function VideosTab() {
  const [items, setItems] = useState<VideoEntry[]>([])
  const [loading, setLoading] = useState(true)
  function load() {
    setLoading(true)
    adminApi.getVideos()
      .then((r) => {
        const data = r.data
        setItems((Array.isArray(data) ? data : data.items || []) as VideoEntry[])
      })
      .finally(() => setLoading(false))
  }
  useEffect(load, [])
  async function remove(id: number) {
    if (!confirm('Удалить видео и все его вопросы?')) return
    await adminApi.deleteVideo(id)
    toast.success('Удалено')
    load()
  }
  async function exportCsv() {
    try {
      const r = await adminApi.exportCsv()
      const blob = new Blob([r.data as Blob], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `interviewhub_export_${Date.now()}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch { toast.error('Ошибка экспорта') }
  }
  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm font-medium">Всего: {items.length}</span>
          <Button size="sm" variant="outline" onClick={exportCsv}>
            <Download className="h-4 w-4" /> Экспорт CSV
          </Button>
        </div>
        {loading ? <Loader2 className="mx-auto h-6 w-6 animate-spin" /> : (
          <div className="grid gap-2 sm:grid-cols-2">
            {items.map((v) => (
              <div key={v.id} className="flex items-center gap-3 rounded-lg border border-border/50 p-3">
                {v.thumbnail_url && <img src={v.thumbnail_url} alt="" className="h-12 w-20 rounded object-cover" />}
                <div className="flex-1 min-w-0">
                  <p className="line-clamp-2 text-sm font-medium">{v.title}</p>
                  <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                    {v.platform && <Badge variant="outline" className="text-[10px]">{v.platform}</Badge>}
                    {v.questions_count != null && <span>{v.questions_count} вопросов</span>}
                  </div>
                </div>
                <Button size="icon" variant="ghost" onClick={() => remove(v.id)}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function HHTab() {
  const [running, setRunning] = useState(false)
  async function runSync() {
    setRunning(true)
    try {
      await adminApi.runHHSync()
      toast.success('Синхронизация запущена')
    } catch { toast.error('Ошибка запуска') } finally { setRunning(false) }
  }
  return (
    <Card>
      <CardContent className="p-6">
        <h3 className="text-base font-semibold">Sync HH-навыков</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Запускает синхронизацию навыков из вакансий HH.ru. Может занять несколько минут.
        </p>
        <Button onClick={runSync} disabled={running} className="mt-4" variant="gradient">
          {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Запустить sync
        </Button>
      </CardContent>
    </Card>
  )
}

function statusVariant(s: string | undefined): 'success' | 'warning' | 'destructive' | 'info' | 'secondary' {
  if (s === 'approved' || s === 'completed') return 'success'
  if (s === 'rejected') return 'destructive'
  if (s === 'processing') return 'info'
  if (s === 'pending') return 'warning'
  return 'secondary'
}
