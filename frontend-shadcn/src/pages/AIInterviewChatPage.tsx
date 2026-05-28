import { useEffect, useRef, useState, type FormEvent } from 'react'
import { motion } from 'framer-motion'
import { Bot, Loader2, Play, Send, Square, User as UserIcon, Sparkles, History } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { PageHeader } from '@/components/layout/page-header'
import { chatApi } from '@/api'
import type { ChatMessage } from '@/types'
import { cn, formatDateTime } from '@/lib/utils'

const topics = [
  'JavaScript',
  'TypeScript',
  'React',
  'Vue',
  'Node.js',
  'Python',
  'Go',
  'Rust',
  'System Design',
  'SQL/PostgreSQL',
  'Docker/K8s',
  'ML/AI',
  'Алгоритмы',
]

const difficulties = [
  { v: 'junior', l: 'Junior' },
  { v: 'middle', l: 'Middle' },
  { v: 'senior', l: 'Senior' },
]

interface HistoryEntry {
  interview_id: string | number
  topic?: string
  difficulty?: string
  status?: string
  created_at?: string
  summary?: string
}

export function AIInterviewChatPage() {
  const [topic, setTopic] = useState(topics[0])
  const [difficulty, setDifficulty] = useState('middle')
  const [interviewId, setInterviewId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [starting, setStarting] = useState(false)
  const [sending, setSending] = useState(false)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const scroller = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatApi.history(10).then((r) => {
      const data = r.data
      setHistory((Array.isArray(data) ? data : data.items || []) as HistoryEntry[])
    }).catch(() => undefined)
  }, [])

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  async function start() {
    setStarting(true)
    try {
      const r = await chatApi.start(topic, difficulty)
      const id = String(r.data.interview_id || r.data.id)
      setInterviewId(id)
      const greeting = (r.data.message || r.data.greeting || `Привет! Готов начать собеседование по ${topic} (${difficulty}).`)
      setMessages([{ role: 'assistant', content: greeting }])
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(detail || 'Не удалось начать интервью')
    } finally {
      setStarting(false)
    }
  }

  async function send(e: FormEvent) {
    e.preventDefault()
    if (!interviewId || !draft.trim() || sending) return
    const userMsg: ChatMessage = { role: 'user', content: draft.trim() }
    setMessages((m) => [...m, userMsg])
    setDraft('')
    setSending(true)
    try {
      const r = await chatApi.send(interviewId, userMsg.content)
      const reply = r.data.message || r.data.reply || r.data.content || ''
      setMessages((m) => [...m, { role: 'assistant', content: String(reply) }])
    } catch {
      toast.error('Ошибка отправки сообщения')
      setMessages((m) => [...m, { role: 'assistant', content: 'Извините, не удалось сгенерировать ответ.' }])
    } finally {
      setSending(false)
    }
  }

  async function end() {
    if (!interviewId) return
    try {
      const r = await chatApi.end(interviewId)
      const summary = r.data.summary || r.data.feedback || 'Сессия завершена.'
      setMessages((m) => [...m, { role: 'assistant', content: `📝 Итоги:\n${summary}` }])
      setInterviewId(null)
    } catch {
      toast.error('Не удалось завершить')
    }
  }

  return (
    <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_320px]">
      <div>
        <PageHeader
          icon={<Bot className="h-5 w-5" />}
          title="AI Interview"
          description="Чат-бот проведёт интервью по выбранной теме и даст обратную связь"
        />

        {!interviewId ? (
          <Card>
            <CardContent className="flex flex-col gap-4 p-6">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <span className="text-sm font-medium">Тема</span>
                  <Select value={topic} onValueChange={setTopic}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {topics.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-sm font-medium">Уровень</span>
                  <Select value={difficulty} onValueChange={setDifficulty}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {difficulties.map((d) => <SelectItem key={d.v} value={d.v}>{d.l}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button onClick={start} disabled={starting} variant="gradient" size="lg">
                {starting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                Начать собеседование
              </Button>
              <p className="text-center text-xs text-muted-foreground">
                AI задаст несколько вопросов и оценит ваши ответы. История сохраняется.
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <div className="flex items-center justify-between border-b border-border/60 p-4">
                <div className="flex items-center gap-2">
                  <Badge variant="gradient">{topic}</Badge>
                  <Badge variant="outline">{difficulty}</Badge>
                </div>
                <Button variant="outline" size="sm" onClick={end}>
                  <Square className="h-4 w-4" /> Завершить
                </Button>
              </div>

              <div ref={scroller} className="flex max-h-[60svh] flex-col gap-4 overflow-y-auto p-6">
                {messages.map((m, i) => <ChatBubble key={i} msg={m} />)}
                {sending && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="h-3 w-3 animate-spin" /> AI печатает…
                  </div>
                )}
              </div>

              <form onSubmit={send} className="flex items-center gap-2 border-t border-border/60 p-3">
                <Input
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Ваш ответ…"
                  autoFocus
                />
                <Button type="submit" disabled={!draft.trim() || sending} variant="default">
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </CardContent>
          </Card>
        )}
      </div>

      <aside>
        <Card>
          <CardContent className="p-4">
            <div className="mb-3 flex items-center gap-2">
              <History className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold">История</h3>
            </div>
            {history.length === 0 ? (
              <p className="text-xs text-muted-foreground">История пуста</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {history.map((h) => (
                  <li key={h.interview_id} className="rounded-lg border border-border/40 bg-card/40 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <Badge variant="outline" className="text-[10px]">{h.topic || '—'}</Badge>
                      <span className="text-[10px] text-muted-foreground">{formatDateTime(h.created_at || '')}</span>
                    </div>
                    {h.summary && <p className="mt-1 line-clamp-2 text-xs">{h.summary}</p>}
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

function ChatBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('flex gap-3', isUser && 'flex-row-reverse')}
    >
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className={cn(
          'text-xs font-bold',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-gradient-to-br from-violet-500 to-cyan-500 text-white'
        )}>
          {isUser ? <UserIcon className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>
      <div className={cn(
        'max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap',
        isUser ? 'bg-primary text-primary-foreground rounded-tr-sm' : 'bg-muted rounded-tl-sm'
      )}>
        {msg.content}
      </div>
    </motion.div>
  )
}
