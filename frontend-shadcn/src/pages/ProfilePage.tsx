import { useEffect, useState, type FormEvent } from 'react'
import { Code, Loader2, Save, User as UserIcon, AtSign } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { PageHeader } from '@/components/layout/page-header'
import { useAuthStore } from '@/store/auth'
import { formatDate } from '@/lib/utils'

export function ProfilePage() {
  const { user, refreshProfile, updateProfile } = useAuthStore()
  const [bio, setBio] = useState('')
  const [github, setGithub] = useState('')
  const [email, setEmail] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    refreshProfile()
  }, [refreshProfile])

  useEffect(() => {
    if (!user) return
    setBio(user.bio || '')
    setGithub(user.github_url || '')
    setEmail(user.email || '')
  }, [user])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await updateProfile({ bio, github_url: github, email })
      toast.success('Профиль обновлён')
    } catch {
      toast.error('Не удалось сохранить')
    } finally {
      setSaving(false)
    }
  }

  if (!user) return null

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <PageHeader
        icon={<UserIcon className="h-5 w-5" />}
        title="Профиль"
        description="Информация о вашем аккаунте и публичных данных"
      />

      <Card className="mb-6">
        <CardContent className="flex flex-wrap items-center gap-5 p-6">
          <Avatar className="h-16 w-16 shadow-md">
            <AvatarFallback className="bg-gradient-to-br from-violet-500 to-cyan-500 text-lg text-white font-bold">
              {user.username.slice(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <h2 className="text-xl font-semibold">{user.username}</h2>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Badge variant={user.role === 'admin' ? 'gradient' : 'secondary'}>
                {user.role === 'admin' ? 'Администратор' : 'Пользователь'}
              </Badge>
              {user.created_at && (
                <span className="text-xs text-muted-foreground">
                  с {formatDate(user.created_at)}
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Редактирование</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <AtSign className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="pl-9"
                />
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="github">GitHub URL</Label>
              <div className="relative">
                <Code className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="github"
                  value={github}
                  onChange={(e) => setGithub(e.target.value)}
                  placeholder="https://github.com/your-handle"
                  className="pl-9"
                />
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="bio">Био</Label>
              <Textarea
                id="bio"
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Расскажите о себе…"
                rows={4}
              />
            </div>
            <Separator />
            <div className="flex justify-end">
              <Button type="submit" disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Сохранить
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
