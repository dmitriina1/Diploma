import { useEffect, useMemo, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, RotateCcw, Sparkles, ChevronLeft, ChevronRight, ListChecks, Trophy, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { PageHeader } from '@/components/layout/page-header'
import { trainerApi, getUserSession } from '@/api'
import type { SM2Card } from '@/types'
import { cn } from '@/lib/utils'

type Grade = 0 | 1 | 2 | 3 | 4 | 5

const grades: Array<{ g: Grade; label: string; key: string; variant: 'destructive' | 'warning' | 'success' }> = [
  { g: 0, label: 'Не вспомнил', key: '1', variant: 'destructive' },
  { g: 2, label: 'С трудом', key: '2', variant: 'warning' },
  { g: 4, label: 'Уверенно', key: '3', variant: 'success' },
  { g: 5, label: 'Идеально', key: '4', variant: 'success' },
]

export function TrainerPage() {
  const userSession = getUserSession()
  const [cards, setCards] = useState<SM2Card[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [flipped, setFlipped] = useState(false)
  const [index, setIndex] = useState(0)
  const [done, setDone] = useState(0)

  const reload = useCallback(() => {
    setLoading(true)
    trainerApi
      .getCards(userSession)
      .then((r) => {
        const data = r.data
        const list = (Array.isArray(data) ? data : data.items || data.cards || []) as SM2Card[]
        setCards(list)
        setIndex(0)
        setFlipped(false)
      })
      .catch(() => toast.error('Не удалось загрузить тренажёр'))
      .finally(() => setLoading(false))
  }, [userSession])

  useEffect(() => {
    reload()
  }, [reload])

  const dueCards = useMemo(() => {
    const now = Date.now()
    return cards.filter((c) => !c.next_review_date || new Date(c.next_review_date).getTime() <= now)
  }, [cards])

  const card = dueCards[index]
  const total = dueCards.length

  const grade = useCallback(async (g: Grade) => {
    if (!card || submitting) return
    setSubmitting(true)
    try {
      await trainerApi.reviewCard({ question_id: card.question_id, grade: g, user_session: userSession })
      setDone((d) => d + 1)
      if (index + 1 < dueCards.length) {
        setIndex((i) => i + 1)
        setFlipped(false)
      } else {
        toast.success('Сессия завершена!')
        reload()
      }
    } catch {
      toast.error('Не удалось сохранить оценку')
    } finally {
      setSubmitting(false)
    }
  }, [card, submitting, userSession, index, dueCards.length, reload])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLElement && ['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault()
        setFlipped((f) => !f)
      }
      if (e.key === 'ArrowRight' && card) {
        setIndex((i) => Math.min(i + 1, total - 1))
        setFlipped(false)
      }
      if (e.key === 'ArrowLeft') {
        setIndex((i) => Math.max(i - 1, 0))
        setFlipped(false)
      }
      if (flipped && card && ['1', '2', '3', '4'].includes(e.key)) {
        const idx = parseInt(e.key, 10) - 1
        const g = grades[idx]?.g
        if (g != null) grade(g)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [card, total, flipped, grade])

  async function reset() {
    if (!confirm('Сбросить весь прогресс тренажёра?')) return
    try {
      await trainerApi.resetCards(userSession)
      toast.success('Прогресс сброшен')
      reload()
    } catch {
      toast.error('Ошибка сброса')
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <PageHeader
        icon={<Brain className="h-5 w-5" />}
        title="SM-2 Тренажёр"
        description="Интервальное повторение по алгоритму SuperMemo. Пробел — перевернуть карточку, цифры 1–4 — оценка."
        actions={
          <Button variant="outline" size="sm" onClick={reset} disabled={loading}>
            <RotateCcw className="h-4 w-4" /> Сбросить
          </Button>
        }
      />

      {loading ? (
        <Card><CardContent className="flex items-center justify-center p-20"><Loader2 className="h-8 w-8 animate-spin text-primary" /></CardContent></Card>
      ) : total === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-20 text-center">
            <Trophy className="h-12 w-12 text-emerald-500" />
            <div>
              <h2 className="text-xl font-semibold">Все карточки на сегодня готовы!</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Возвращайтесь завтра или добавьте новые вопросы из каталога
              </p>
            </div>
            <Button variant="default" onClick={reload}>
              <RefreshCw className="h-4 w-4" /> Обновить
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="mb-4 flex items-center justify-between text-sm">
            <Badge variant="outline" className="gap-1">
              <ListChecks className="h-3.5 w-3.5" /> {index + 1} / {total}
            </Badge>
            <span className="text-muted-foreground">Завершено: {done}</span>
          </div>
          <Progress value={total ? (index / total) * 100 : 0} className="mb-6" />

          <div className="relative perspective-[2000px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={card?.question_id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.25 }}
              >
                <button
                  type="button"
                  onClick={() => setFlipped((f) => !f)}
                  className="group relative block w-full text-left"
                  style={{ transformStyle: 'preserve-3d' }}
                >
                  <motion.div
                    className="relative h-72 w-full"
                    animate={{ rotateY: flipped ? 180 : 0 }}
                    transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                    style={{ transformStyle: 'preserve-3d' }}
                  >
                    {/* Front */}
                    <Card
                      className="absolute inset-0 flex flex-col justify-between overflow-hidden p-6 transition-shadow group-hover:shadow-lg"
                      style={{ backfaceVisibility: 'hidden' }}
                    >
                      <div>
                        <Badge variant="secondary" className="mb-2">Вопрос</Badge>
                        <p className="text-lg font-semibold leading-snug">{card?.question_text || card?.question?.text}</p>
                      </div>
                      <p className="text-xs text-muted-foreground">Нажмите карточку или Space, чтобы увидеть ответ</p>
                    </Card>

                    {/* Back */}
                    <Card
                      className="absolute inset-0 flex flex-col justify-between overflow-hidden border-primary/30 p-6"
                      style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
                    >
                      <div>
                        <Badge variant="gradient" className="mb-2 gap-1">
                          <Sparkles className="h-3 w-3" /> Ответ
                        </Badge>
                        <p className="overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-foreground/90 max-h-48">
                          {card?.question?.answer || 'Эталонный ответ отсутствует'}
                        </p>
                      </div>
                      <p className="text-xs text-muted-foreground">Оцените ваш ответ цифрами 1–4</p>
                    </Card>
                  </motion.div>
                </button>
              </motion.div>
            </AnimatePresence>
          </div>

          <div className={cn('mt-6 grid grid-cols-2 gap-2 sm:grid-cols-4', !flipped && 'pointer-events-none opacity-50')}>
            {grades.map((g) => (
              <Button
                key={g.g}
                variant={g.variant === 'destructive' ? 'destructive' : 'outline'}
                onClick={() => grade(g.g)}
                disabled={submitting || !flipped}
                className="flex h-auto flex-col gap-0.5 py-3"
              >
                <span className="text-xs uppercase opacity-60">{g.key}</span>
                <span>{g.label}</span>
              </Button>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              disabled={index === 0}
              onClick={() => { setIndex((i) => Math.max(0, i - 1)); setFlipped(false) }}
            >
              <ChevronLeft className="h-4 w-4" /> Предыдущая
            </Button>
            <Button
              variant="ghost"
              size="sm"
              disabled={index >= total - 1}
              onClick={() => { setIndex((i) => Math.min(total - 1, i + 1)); setFlipped(false) }}
            >
              Следующая <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </>
      )}
    </div>
  )
}
