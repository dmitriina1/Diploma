import { useEffect, useState } from 'react'
import { Mic2, Loader2, Play, ListChecks, Sparkles, Check, ChevronRight, History } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Progress } from '@/components/ui/progress'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { PageHeader } from '@/components/layout/page-header'
import { mockApi } from '@/api'
import { formatDateTime } from '@/lib/utils'
import type { MockInterviewSession, Question } from '@/types'

const counts = [3, 5, 10, 15]
const levels = [
  { v: 'junior', l: 'Junior' },
  { v: 'middle', l: 'Middle' },
  { v: 'senior', l: 'Senior' },
]

export function MockInterviewPage() {
  const [profession, setProfession] = useState('frontend')
  const [level, setLevel] = useState('middle')
  const [count, setCount] = useState(5)
  const [session, setSession] = useState<MockInterviewSession | null>(null)
  const [answers, setAnswers] = useState<Record<number | string, string>>({})
  const [step, setStep] = useState(0)
  const [starting, setStarting] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ score?: number; feedback?: string } | null>(null)
  const [history, setHistory] = useState<MockInterviewSession[]>([])

  useEffect(() => {
    mockApi.history().then((r) => {
      const data = r.data
      setHistory((Array.isArray(data) ? data : data.items || []) as MockInterviewSession[])
    }).catch(() => undefined)
  }, [])

  async function start() {
    setStarting(true)
    setResult(null)
    try {
      const r = await mockApi.start({ profession, difficulty: level, questions_count: count })
      setSession(r.data as MockInterviewSession)
      setAnswers({})
      setStep(0)
    } catch {
      toast.error('Не удалось начать сессию')
    } finally {
      setStarting(false)
    }
  }

  async function finish() {
    if (!session) return
    setSubmitting(true)
    try {
      const id = session.interview_id || session.id || ''
      const payload = {
        answers: Object.entries(answers).map(([question_id, text]) => ({ question_id, text })),
      }
      const r = await mockApi.submit(id, payload)
      setResult(r.data as { score?: number; feedback?: string })
      toast.success('Mock-интервью завершено')
    } catch {
      toast.error('Не удалось отправить ответы')
    } finally {
      setSubmitting(false)
    }
  }

  const questions: Question[] = (session?.questions || []) as Question[]
  const current = questions[step]
  const total = questions.length

  return (
    <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_300px]">
      <div>
        <PageHeader
          icon={<Mic2 className="h-5 w-5" />}
          title="Mock-собеседование"
          description="Реалистичная симуляция: набор вопросов по уровню и теме с финальной оценкой"
        />

        {!session && !result && (
          <Card>
            <CardContent className="grid gap-4 p-6 sm:grid-cols-3">
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium">Профессия</span>
                <Select value={profession} onValueChange={setProfession}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {['frontend', 'backend', 'fullstack', 'devops', 'data', 'mobile', 'qa'].map((p) => (
                      <SelectItem key={p} value={p}>{p}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium">Уровень</span>
                <Select value={level} onValueChange={setLevel}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {levels.map((l) => <SelectItem key={l.v} value={l.v}>{l.l}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium">Вопросов</span>
                <Select value={String(count)} onValueChange={(v) => setCount(parseInt(v, 10))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {counts.map((c) => <SelectItem key={c} value={String(c)}>{c}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="sm:col-span-3">
                <Button onClick={start} disabled={starting} size="lg" variant="gradient" className="w-full sm:w-auto">
                  {starting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  Начать сессию
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {session && current && !result && (
          <Card className="overflow-hidden">
            <CardContent className="p-6">
              <div className="mb-4 flex items-center justify-between">
                <Badge variant="outline" className="gap-1">
                  <ListChecks className="h-3 w-3" /> {step + 1} / {total}
                </Badge>
                <Badge variant="gradient">{level}</Badge>
              </div>
              <Progress value={((step) / total) * 100} className="mb-6" />
              <motion.div
                key={current.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <h2 className="text-lg font-semibold leading-snug sm:text-xl">{current.text}</h2>
                <Textarea
                  value={answers[current.id] || ''}
                  onChange={(e) => setAnswers((a) => ({ ...a, [current.id]: e.target.value }))}
                  placeholder="Ваш ответ…"
                  rows={6}
                  className="mt-4"
                />
              </motion.div>
              <div className="mt-4 flex items-center justify-between">
                <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
                  Назад
                </Button>
                {step < total - 1 ? (
                  <Button onClick={() => setStep((s) => s + 1)}>
                    Дальше <ChevronRight className="h-4 w-4" />
                  </Button>
                ) : (
                  <Button onClick={finish} disabled={submitting} variant="gradient">
                    {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                    Завершить
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {result && (
          <Card className="overflow-hidden border-emerald-500/30">
            <CardContent className="p-6">
              <div className="mb-3 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-emerald-500" />
                <h2 className="text-xl font-semibold">Результат</h2>
              </div>
              {result.score != null && (
                <div className="mb-4">
                  <span className="text-4xl font-bold gradient-text">{result.score}</span>
                  <span className="text-sm text-muted-foreground"> / 100</span>
                </div>
              )}
              {result.feedback && (
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{result.feedback}</p>
              )}
              <Button className="mt-4" variant="outline" onClick={() => { setSession(null); setResult(null) }}>
                Новая сессия
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      <aside>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <History className="h-4 w-4 text-primary" /> История
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs">
            {history.length === 0 ? (
              <p className="text-muted-foreground">Пока пусто</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {history.slice(0, 8).map((h, idx) => (
                  <li key={String(h.id || idx)} className="rounded-lg border border-border/40 bg-card/40 p-2.5">
                    <div className="flex items-center justify-between">
                      <Badge variant="outline" className="text-[10px]">{h.level || '—'}</Badge>
                      <span className="text-[10px] text-muted-foreground">{formatDateTime(h.created_at || '')}</span>
                    </div>
                    {h.score != null && <p className="mt-1 text-sm font-semibold">{h.score} / 100</p>}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </aside>
    </div>
  )
}
