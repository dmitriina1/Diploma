import { useEffect, useMemo, useState } from 'react'
import { TrendingUp, Loader2, Filter } from 'lucide-react'
import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/layout/page-header'
import { contentApi } from '@/api'
import type { HHSkill, Profession } from '@/types'

type Source = 'skills' | 'description' | 'title'

export function HHRequirementsPage() {
  const [skills, setSkills] = useState<HHSkill[]>([])
  const [professions, setProfessions] = useState<Profession[]>([])
  const [profession, setProfession] = useState<string>('all')
  const [sources, setSources] = useState<Source[]>(['skills'])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    contentApi
      .getHHProfessions()
      .then((r) => {
        const data = r.data
        setProfessions((Array.isArray(data) ? data : data.items || []) as Profession[])
      })
      .catch(() => undefined)
  }, [])

  useEffect(() => {
    setLoading(true)
    contentApi
      .getHHSkills(profession === 'all' ? null : profession, 1, 200, sources.length ? sources : null)
      .then((r) => {
        const data = r.data
        setSkills((Array.isArray(data) ? data : data.items || []) as HHSkill[])
      })
      .finally(() => setLoading(false))
  }, [profession, sources])

  const max = useMemo(() => Math.max(...skills.map((s) => s.count || 0), 1), [skills])

  function toggleSource(s: Source) {
    setSources((arr) => arr.includes(s) ? arr.filter((x) => x !== s) : [...arr, s])
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <PageHeader
        icon={<TrendingUp className="h-5 w-5" />}
        title="HH-навыки"
        description="Самые востребованные навыки из вакансий HH.ru — обновляются автоматически"
      />

      <Card className="mb-6">
        <CardContent className="grid gap-3 p-4 sm:grid-cols-[1fr_auto]">
          <Select value={profession} onValueChange={setProfession}>
            <SelectTrigger>
              <SelectValue placeholder="Профессия" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все профессии</SelectItem>
              {professions.map((p) => (
                <SelectItem key={p.slug} value={p.slug}>{p.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground hidden sm:inline">
              <Filter className="mr-1 inline h-3 w-3" /> Источник:
            </span>
            {(['skills', 'description', 'title'] as const).map((s) => (
              <Button
                key={s}
                size="sm"
                variant={sources.includes(s) ? 'default' : 'outline'}
                onClick={() => toggleSource(s)}
              >
                {s === 'skills' ? 'Навыки' : s === 'description' ? 'Описание' : 'Заголовок'}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
      ) : skills.length === 0 ? (
        <Card><CardContent className="py-16 text-center text-sm text-muted-foreground">Навыки не найдены</CardContent></Card>
      ) : (
        <Card>
          <CardContent className="p-4 sm:p-6">
            <div className="flex flex-col gap-2">
              {skills.map((s, idx) => {
                const pct = ((s.count || 0) / max) * 100
                return (
                  <motion.div
                    key={`${s.name}-${idx}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: Math.min(idx * 0.01, 0.4) }}
                    className="flex items-center gap-3"
                  >
                    <div className="flex w-44 shrink-0 items-center gap-2 truncate" title={s.name}>
                      <span className="text-xs text-muted-foreground tabular-nums">{idx + 1}.</span>
                      <span className="truncate text-sm font-medium">{s.name}</span>
                    </div>
                    <div className="relative h-7 flex-1 overflow-hidden rounded-md bg-muted">
                      <div
                        className="absolute inset-y-0 left-0 rounded-md bg-gradient-to-r from-primary/60 to-cyan-500/60 transition-all"
                        style={{ width: `${pct}%` }}
                      />
                      <span className="absolute inset-y-0 right-2 flex items-center text-xs font-semibold tabular-nums">
                        {s.count}
                      </span>
                    </div>
                    <Badge variant="outline" className="hidden text-[10px] sm:inline-flex">
                      {s.source}
                    </Badge>
                  </motion.div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
