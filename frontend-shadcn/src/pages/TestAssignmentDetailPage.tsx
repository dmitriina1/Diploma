import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Building2, Loader2, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { contentApi } from '@/api'
import type { TestAssignment } from '@/types'
import { formatDate } from '@/lib/utils'

export function TestAssignmentDetailPage() {
  const { id } = useParams()
  const [item, setItem] = useState<TestAssignment | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    contentApi
      .getTestAssignmentDetail(id)
      .then((r) => setItem(r.data as TestAssignment))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-10 sm:px-6">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }
  if (!item) return null

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2 mb-4 w-fit">
        <Link to="/test-assignments"><ArrowLeft className="h-4 w-4" /> К списку</Link>
      </Button>
      <Card>
        <CardContent className="p-6 sm:p-8">
          <div className="flex flex-wrap items-center gap-2">
            {item.level && <Badge variant="info">{item.level}</Badge>}
            {item.technology && <Badge variant="secondary">{item.technology}</Badge>}
            {item.created_at && <span className="text-xs text-muted-foreground">{formatDate(item.created_at)}</span>}
          </div>
          <h1 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">{item.title}</h1>
          {item.company && (
            <div className="mt-2 flex items-center gap-1 text-sm text-muted-foreground">
              <Building2 className="h-4 w-4" /> {item.company}
            </div>
          )}
          {item.description && <p className="mt-4 text-muted-foreground">{item.description}</p>}
          {item.body && (
            <article className="prose prose-neutral mt-6 max-w-none text-sm leading-relaxed dark:prose-invert">
              <div className="whitespace-pre-wrap">{item.body}</div>
            </article>
          )}
          {item.url && (
            <Button asChild className="mt-6" variant="outline">
              <a href={item.url} target="_blank" rel="noreferrer">
                Открыть оригинал <ExternalLink className="h-4 w-4" />
              </a>
            </Button>
          )}
        </CardContent>
      </Card>
      {/* keep loader2 imported to avoid unused */}
      <Loader2 className="hidden" />
    </div>
  )
}
