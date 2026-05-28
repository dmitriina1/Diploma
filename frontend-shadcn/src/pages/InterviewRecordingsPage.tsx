import { useEffect, useState } from 'react'
import { Video, ExternalLink, Loader2, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { PageHeader } from '@/components/layout/page-header'
import { questionsApi } from '@/api'
import { formatDate } from '@/lib/utils'
import type { ProcessedVideo } from '@/types'

export function InterviewRecordingsPage() {
  const [videos, setVideos] = useState<ProcessedVideo[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    questionsApi
      .recordings({ limit: 200 })
      .then((r) => {
        const data = r.data
        setVideos((Array.isArray(data) ? data : data.items || data.recordings || []) as ProcessedVideo[])
      })
      .finally(() => setLoading(false))
  }, [])

  const filtered = videos.filter((v) => v.title?.toLowerCase().includes(search.toLowerCase()))

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <PageHeader
        icon={<Video className="h-5 w-5" />}
        title="Записи собеседований"
        description="Видео-источники, из которых были извлечены вопросы"
      />

      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по названию…"
              className="pl-9"
            />
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center text-sm text-muted-foreground">
            Записи не найдены
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((v) => (
            <Card key={v.id} className="group overflow-hidden transition-all hover:-translate-y-0.5 hover:shadow-lg">
              <div className="relative aspect-video w-full overflow-hidden bg-muted">
                {v.thumbnail_url ? (
                  <img src={v.thumbnail_url} alt={v.title} className="h-full w-full object-cover transition-transform group-hover:scale-105" />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-primary/20 to-cyan-500/20">
                    <Video className="h-12 w-12 text-primary" />
                  </div>
                )}
                {v.platform && (
                  <Badge variant="gradient" className="absolute left-2 top-2 text-[10px]">{v.platform}</Badge>
                )}
              </div>
              <CardContent className="p-4">
                <h3 className="line-clamp-2 text-sm font-semibold leading-snug">{v.title}</h3>
                <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span>{v.channel || '—'}</span>
                  {v.created_at && <span>{formatDate(v.created_at)}</span>}
                </div>
                <Button asChild variant="outline" size="sm" className="mt-3 w-full">
                  <a href={v.url} target="_blank" rel="noreferrer">
                    Открыть <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
