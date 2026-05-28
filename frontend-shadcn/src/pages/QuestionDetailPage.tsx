import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  Bookmark,
  Loader2,
  MessageSquare,
  Send,
  ThumbsDown,
  ThumbsUp,
  Video as VideoIcon,
  Sparkles,
} from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { contentApi, getUserSession, questionsApi } from '@/api'
import type { Question } from '@/types'
import { formatDateTime, truncate } from '@/lib/utils'
import { useAuthStore } from '@/store/auth'

interface UserAnswer {
  id: number
  text: string
  votes: number
  user_session?: string
  is_anonymous?: boolean
  created_at?: string
  user_vote?: 1 | -1 | 0
}

export function QuestionDetailPage() {
  const { id } = useParams()
  const { isAuthenticated } = useAuthStore()
  const [question, setQuestion] = useState<Question | null>(null)
  const [similar, setSimilar] = useState<Question[]>([])
  const [answers, setAnswers] = useState<UserAnswer[]>([])
  const [loading, setLoading] = useState(true)
  const [posting, setPosting] = useState(false)
  const [bookmarkLoading, setBookmarkLoading] = useState(false)
  const [bookmarked, setBookmarked] = useState(false)
  const [draft, setDraft] = useState('')

  const userSession = getUserSession()

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      questionsApi.detail(id),
      questionsApi.similar({ question_id: id, limit: 5 }).catch(() => ({ data: [] })),
      contentApi.getUserAnswers(id).catch(() => ({ data: [] })),
    ])
      .then(([q, sim, ans]) => {
        setQuestion(q.data as Question)
        const simData = sim.data
        setSimilar((Array.isArray(simData) ? simData : simData.items || []) as Question[])
        const ansData = ans.data
        setAnswers((Array.isArray(ansData) ? ansData : ansData.items || []) as UserAnswer[])
      })
      .catch(() => toast.error('Не удалось загрузить вопрос'))
      .finally(() => setLoading(false))
  }, [id])

  async function postAnswer() {
    if (!draft.trim() || !id) return
    setPosting(true)
    try {
      const r = await contentApi.postUserAnswer(id, { user_session: userSession, text: draft.trim(), is_anonymous: !isAuthenticated })
      const newAns = r.data as UserAnswer
      setAnswers((a) => [newAns, ...a])
      setDraft('')
      toast.success('Ответ отправлен')
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(detail || 'Ошибка отправки')
    } finally {
      setPosting(false)
    }
  }

  async function vote(answerId: number, value: 1 | -1) {
    try {
      await contentApi.voteAnswer(answerId, { user_session: userSession, vote: value })
      setAnswers((arr) => arr.map((a) => {
        if (a.id !== answerId) return a
        const prev = a.user_vote || 0
        const delta = value === prev ? -prev : value - prev
        return { ...a, votes: (a.votes || 0) + delta, user_vote: value === prev ? 0 : value }
      }))
    } catch {
      toast.error('Не удалось проголосовать')
    }
  }

  async function bookmark() {
    if (!id) return
    setBookmarkLoading(true)
    try {
      await contentApi.addBookmark({ question_id: Number(id), user_session: userSession })
      setBookmarked(true)
      toast.success('Добавлено в закладки')
    } catch {
      toast.error('Ошибка закладки')
    } finally {
      setBookmarkLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4 px-4 py-10 sm:px-6">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  if (!question) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-6">
        <h1 className="text-xl font-semibold">Вопрос не найден</h1>
        <Button asChild className="mt-4" variant="outline">
          <Link to="/interview-questions">К каталогу</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2 w-fit">
        <Link to="/interview-questions">
          <ArrowLeft className="h-4 w-4" /> К каталогу
        </Link>
      </Button>

      <Card className="overflow-hidden">
        <CardContent className="p-6 sm:p-8">
          <div className="flex flex-wrap items-center gap-2">
            {question.technology && <Badge variant="info">{question.technology}</Badge>}
            {(question.tags || []).slice(0, 5).map((t) => (
              <Badge key={t} variant="secondary">{t}</Badge>
            ))}
            {question.difficulty != null && <Badge>{String(question.difficulty)}</Badge>}
          </div>
          <h1 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
            {question.text}
          </h1>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={bookmark}
              disabled={bookmarkLoading || bookmarked}
            >
              {bookmarkLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Bookmark className="h-4 w-4" />}
              {bookmarked ? 'В закладках' : 'В закладки'}
            </Button>
            {question.probability != null && (
              <Badge variant="gradient" className="gap-1">
                <Sparkles className="h-3 w-3" /> Вероятность: {(question.probability * (question.probability < 1 ? 100 : 1)).toFixed(0)}%
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {question.answer && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Эталонный ответ</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">{question.answer}</p>
          </CardContent>
        </Card>
      )}

      {(question.videos || []).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <VideoIcon className="h-4 w-4" /> Где упоминается
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {(question.videos || []).map((v) => (
              <a
                key={v.id}
                href={v.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between gap-3 rounded-lg border border-border/50 p-3 transition-colors hover:border-primary/30"
              >
                <div className="flex flex-col">
                  <span className="line-clamp-1 text-sm font-medium">{v.title}</span>
                  <span className="text-xs text-muted-foreground">{v.platform || v.channel || ''}</span>
                </div>
                <ArrowLeft className="h-4 w-4 rotate-180 text-muted-foreground" />
              </a>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <MessageSquare className="h-4 w-4" /> Ответы пользователей ({answers.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-2">
            <Textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Поделитесь своим вариантом ответа…"
              rows={4}
            />
            <div className="flex items-center justify-end">
              <Button onClick={postAnswer} disabled={!draft.trim() || posting}>
                {posting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Отправить
              </Button>
            </div>
          </div>
          <Separator />
          {answers.length === 0 && (
            <p className="text-center text-sm text-muted-foreground py-6">
              Пока нет ответов. Будьте первым!
            </p>
          )}
          {answers.map((a) => (
            <motion.div
              key={a.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-lg border border-border/40 bg-card/50 p-4"
            >
              <div className="flex items-start gap-3">
                <div className="flex flex-col items-center gap-0.5">
                  <Button
                    size="icon"
                    variant={a.user_vote === 1 ? 'default' : 'ghost'}
                    onClick={() => vote(a.id, 1)}
                    className="h-7 w-7"
                  >
                    <ThumbsUp className="h-3.5 w-3.5" />
                  </Button>
                  <span className="text-xs font-semibold">{a.votes || 0}</span>
                  <Button
                    size="icon"
                    variant={a.user_vote === -1 ? 'default' : 'ghost'}
                    onClick={() => vote(a.id, -1)}
                    className="h-7 w-7"
                  >
                    <ThumbsDown className="h-3.5 w-3.5" />
                  </Button>
                </div>
                <div className="flex-1">
                  <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{a.is_anonymous ? 'Аноним' : truncate(a.user_session || 'user', 12)}</span>
                    {a.created_at && <span>· {formatDateTime(a.created_at)}</span>}
                  </div>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{a.text}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </CardContent>
      </Card>

      {similar.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Похожие вопросы</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 sm:grid-cols-2">
            {similar.map((s) => (
              <Link
                key={s.id}
                to={`/question/${s.id}`}
                className="rounded-lg border border-border/40 bg-card/50 p-3 transition-colors hover:border-primary/30"
              >
                <p className="line-clamp-2 text-sm">{s.text}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {s.technology && <Badge variant="info" className="text-[10px]">{s.technology}</Badge>}
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
