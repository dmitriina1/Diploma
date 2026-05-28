import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Loader2, LogIn, UserPlus, AtSign, Lock, User as UserIcon, ArrowLeft } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { GridPattern } from '@/components/effects/grid-pattern'
import { useAuthStore } from '@/store/auth'
import { BrandLogo } from '@/components/layout/brand-logo'
import { ThemeToggle } from '@/components/layout/theme-toggle'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, register, loading } = useAuthStore()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const redirectTo = ((location.state as { from?: string } | null)?.from) || '/'

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!username.trim() || !password.trim()) {
      toast.error('Введите логин и пароль')
      return
    }
    try {
      if (mode === 'login') {
        await login({ username: username.trim(), password })
        toast.success('Добро пожаловать!')
      } else {
        await register({ username: username.trim(), password, email: email.trim() || undefined })
        toast.success('Аккаунт создан')
      }
      navigate(redirectTo, { replace: true })
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(detail || 'Ошибка авторизации. Проверьте данные.')
    }
  }

  return (
    <div className="relative flex min-h-svh items-center justify-center overflow-hidden bg-background px-4 py-10">
      <GridPattern
        width={32}
        height={32}
        className="[mask-image:radial-gradient(700px_circle_at_center,white,transparent)] -z-10"
        strokeDasharray="2 2"
      />
      <div className="absolute inset-0 -z-10 bg-gradient-to-tr from-primary/10 via-transparent to-cyan-500/10" />

      <div className="absolute inset-x-0 top-0 z-10 flex items-center justify-between p-4 sm:p-6">
        <BrandLogo />
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link to="/">
              <ArrowLeft className="h-4 w-4" /> На главную
            </Link>
          </Button>
          <ThemeToggle />
        </div>
      </div>

      <Card className="relative w-full max-w-md overflow-hidden border-border/60 backdrop-blur-md">
        <CardContent className="p-8">
          <div className="mb-6 flex flex-col gap-1">
            <h1 className="text-2xl font-bold tracking-tight">
              {mode === 'login' ? 'Войти в InterviewHub' : 'Создать аккаунт'}
            </h1>
            <p className="text-sm text-muted-foreground">
              {mode === 'login'
                ? 'Сохраняйте прогресс, закладки и историю собеседований'
                : 'Бесплатно, без подтверждения email'}
            </p>
          </div>

          <div className="mb-6 inline-flex w-full items-center gap-1 rounded-lg bg-muted p-1 text-sm">
            <button
              type="button"
              onClick={() => setMode('login')}
              className={
                'flex-1 rounded-md px-3 py-1.5 transition-colors ' +
                (mode === 'login' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground')
              }
            >
              Вход
            </button>
            <button
              type="button"
              onClick={() => setMode('register')}
              className={
                'flex-1 rounded-md px-3 py-1.5 transition-colors ' +
                (mode === 'register' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground')
              }
            >
              Регистрация
            </button>
          </div>

          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="username">Логин</Label>
              <div className="relative">
                <UserIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="username"
                  className="pl-9"
                  placeholder="ivanov"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            {mode === 'register' && (
              <div className="flex flex-col gap-2">
                <Label htmlFor="email">Email (опционально)</Label>
                <div className="relative">
                  <AtSign className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    className="pl-9"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                  />
                </div>
              </div>
            )}

            <div className="flex flex-col gap-2">
              <Label htmlFor="password">Пароль</Label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  className="pl-9"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                  required
                  minLength={4}
                />
              </div>
            </div>

            <Button type="submit" variant="gradient" disabled={loading} size="lg" className="mt-2">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Подождите…
                </>
              ) : mode === 'login' ? (
                <>
                  <LogIn className="h-4 w-4" /> Войти
                </>
              ) : (
                <>
                  <UserPlus className="h-4 w-4" /> Создать аккаунт
                </>
              )}
            </Button>
          </form>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            Продолжая, вы соглашаетесь с использованием cookies для сохранения сессии
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
