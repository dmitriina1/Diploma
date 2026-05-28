import { useState, type FormEvent } from 'react'
import { Send, Loader2, Sparkles, Link as LinkIcon, MessageSquare } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/layout/page-header'
import { contentApi, getUserSession } from '@/api'

export function SuggestionsPage() {
  const [url, setUrl] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!url.trim()) {
      toast.error('Укажите URL')
      return
    }
    setSubmitting(true)
    try {
      await contentApi.createSuggestion({
        url: url.trim(),
        description: description.trim() || undefined,
        user_session: getUserSession(),
      })
      setUrl('')
      setDescription('')
      setSuccess(true)
      toast.success('Спасибо! Ваше предложение отправлено')
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(detail || 'Ошибка отправки')
    } finally {
      setSubmitting(false)
    }
  }

  const platforms = [
    { name: 'YouTube', color: 'from-red-500 to-rose-500' },
    { name: 'VK', color: 'from-blue-500 to-cyan-500' },
    { name: 'Rutube', color: 'from-fuchsia-500 to-pink-500' },
    { name: 'OK.ru', color: 'from-orange-500 to-amber-500' },
    { name: 'Vimeo', color: 'from-cyan-500 to-emerald-500' },
    { name: 'Dailymotion', color: 'from-indigo-500 to-violet-500' },
  ]

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <PageHeader
        icon={<Sparkles className="h-5 w-5" />}
        title="Предложить видео"
        description="Поделитесь интересной записью собеседования — модераторы рассмотрят и добавят в обработку"
      />

      <Card className="mb-6">
        <CardContent className="p-6">
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="url">URL видео</Label>
              <div className="relative">
                <LinkIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="url"
                  type="url"
                  className="pl-9"
                  placeholder="https://youtube.com/watch?v=…"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="desc">Комментарий (опционально)</Label>
              <div className="relative">
                <MessageSquare className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Textarea
                  id="desc"
                  className="pl-9"
                  placeholder="Например: интервью на позицию Senior Backend, очень хорошие вопросы по PostgreSQL"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                Видео будет проверено модератором перед обработкой
              </p>
              <Button type="submit" disabled={submitting} variant="gradient">
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Отправить
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {success && (
        <Card className="mb-6 border-emerald-500/40 bg-emerald-500/5">
          <CardContent className="p-4 text-sm">
            <span className="font-semibold text-emerald-600 dark:text-emerald-400">Готово!</span>{' '}
            Ваше предложение в очереди. Мы свяжемся, если потребуется уточнение.
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-6">
          <h3 className="text-sm font-semibold">Поддерживаемые платформы</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {platforms.map((p) => (
              <Badge
                key={p.name}
                className={`bg-gradient-to-r ${p.color} text-white border-transparent`}
              >
                {p.name}
              </Badge>
            ))}
          </div>
          <p className="mt-4 text-xs text-muted-foreground">
            Длительность видео — желательно до 90 минут. Поддерживается русский язык.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
