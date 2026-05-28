import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ClipboardList, Search, Building2, Loader2, ArrowRight } from 'lucide-react'
import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { PageHeader } from '@/components/layout/page-header'
import { contentApi } from '@/api'
import type { TestAssignment } from '@/types'
import { formatDate } from '@/lib/utils'

export function TestAssignmentsPage() {
  const [items, setItems] = useState<TestAssignment[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [level, setLevel] = useState('all')
  const [tech, setTech] = useState('all')

  useEffect(() => {
    contentApi
      .getTestAssignments({ limit: 200 })
      .then((r) => {
        const data = r.data
        setItems((Array.isArray(data) ? data : data.items || []) as TestAssignment[])
      })
      .finally(() => setLoading(false))
  }, [])

  const techs = useMemo(() => Array.from(new Set(items.map((x) => x.technology).filter(Boolean) as string[])), [items])

  const filtered = useMemo(() => {
    return items.filter((it) => {
      if (search && !`${it.title} ${it.description ?? ''} ${it.company ?? ''}`.toLowerCase().includes(search.toLowerCase())) return false
      if (level !== 'all' && (it.level || '').toLowerCase() !== level) return false
      if (tech !== 'all' && it.technology !== tech) return false
      return true
    })
  }, [items, search, level, tech])

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <PageHeader
        icon={<ClipboardList className="h-5 w-5" />}
        title="Тестовые задания"
        description="Реальные задания от компаний для практики и подготовки к финальным этапам"
      />

      <Card className="mb-6">
        <CardContent className="grid gap-3 p-4 sm:grid-cols-[1fr_auto_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по заданию или компании…"
              className="pl-9"
            />
          </div>
          <Select value={level} onValueChange={setLevel}>
            <SelectTrigger className="w-full sm:w-40"><SelectValue placeholder="Уровень" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Любой уровень</SelectItem>
              <SelectItem value="junior">Junior</SelectItem>
              <SelectItem value="middle">Middle</SelectItem>
              <SelectItem value="senior">Senior</SelectItem>
            </SelectContent>
          </Select>
          <Select value={tech} onValueChange={setTech}>
            <SelectTrigger className="w-full sm:w-44"><SelectValue placeholder="Технология" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все технологии</SelectItem>
              {techs.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {loading ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-32 w-full rounded-xl" />)}
        </div>
      ) : filtered.length === 0 ? (
        <Card><CardContent className="py-16 text-center text-sm text-muted-foreground"><Loader2 className="hidden" /> Ничего не найдено</CardContent></Card>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {filtered.map((t, idx) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.03, 0.3) }}
            >
              <Link to={`/test-assignments/${t.id}`} className="block">
                <Card className="group h-full overflow-hidden transition-all hover:-translate-y-0.5 hover:shadow-md hover:border-primary/30">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="line-clamp-2 text-base font-semibold leading-snug">{t.title}</h3>
                      <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground transition-all group-hover:translate-x-0.5 group-hover:text-primary" />
                    </div>
                    {t.company && (
                      <div className="mt-1.5 flex items-center gap-1 text-xs text-muted-foreground">
                        <Building2 className="h-3 w-3" /> {t.company}
                      </div>
                    )}
                    {t.description && <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{t.description}</p>}
                    <div className="mt-3 flex flex-wrap items-center gap-1.5">
                      {t.level && <Badge variant="info" className="text-[10px]">{t.level}</Badge>}
                      {t.technology && <Badge variant="secondary" className="text-[10px]">{t.technology}</Badge>}
                      {t.created_at && <span className="ml-auto text-[10px] text-muted-foreground">{formatDate(t.created_at)}</span>}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
