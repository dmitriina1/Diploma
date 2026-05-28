import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Menu, X, LogIn, LogOut, User as UserIcon, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ThemeToggle } from './theme-toggle'
import { BrandLogo } from './brand-logo'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/auth'

const navItems: Array<{ to: string; label: string; auth?: boolean; admin?: boolean }> = [
  { to: '/', label: 'Главная' },
  { to: '/interview-questions', label: 'Вопросы' },
  { to: '/trainer', label: 'Тренажёр', auth: true },
  { to: '/ai-interview', label: 'AI Interview', auth: true },
  { to: '/mock-interview', label: 'Mock', auth: true },
  { to: '/recordings', label: 'Записи', auth: true },
  { to: '/test-assignments', label: 'Задания', auth: true },
  { to: '/hh-requirements', label: 'HH-навыки' },
  { to: '/suggest', label: 'Предложить' },
  { to: '/admin', label: 'Админ', auth: true, admin: true },
]

export function NavBar() {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuthStore()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const visibleItems = navItems.filter((it) => {
    if (it.admin) return user?.role === 'admin'
    if (it.auth) return isAuthenticated
    return true
  })

  return (
    <header
      className={cn(
        'sticky top-0 z-40 w-full transition-colors',
        scrolled ? 'border-b border-border/60 glass' : 'bg-transparent'
      )}
    >
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6">
        <div className="flex items-center gap-6">
          <BrandLogo />
          <nav className="hidden items-center gap-1 md:flex">
            {visibleItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  cn(
                    'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          {isAuthenticated && user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Профиль" className="rounded-full">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-gradient-to-br from-violet-500 to-cyan-500 text-white text-xs font-bold uppercase">
                      {user.username?.slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col">
                    <span className="font-medium">{user.username}</span>
                    {user.email && <span className="text-xs text-muted-foreground">{user.email}</span>}
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/profile')} className="gap-2">
                  <UserIcon className="h-4 w-4" /> Профиль
                </DropdownMenuItem>
                {user.role === 'admin' && (
                  <DropdownMenuItem onClick={() => navigate('/admin')} className="gap-2">
                    <Shield className="h-4 w-4" /> Админ-панель
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => {
                    logout()
                    navigate('/')
                  }}
                  className="gap-2 text-destructive focus:text-destructive"
                >
                  <LogOut className="h-4 w-4" /> Выйти
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button asChild size="sm" variant="outline" className="hidden sm:inline-flex">
              <Link to="/login">
                <LogIn className="h-4 w-4" /> Войти
              </Link>
            </Button>
          )}
          <Button
            size="icon"
            variant="ghost"
            className="md:hidden"
            onClick={() => setOpen((o) => !o)}
            aria-label="Меню"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {open && (
        <div className="border-t border-border/60 glass md:hidden">
          <nav className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-3">
            {visibleItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'rounded-md px-3 py-2 text-sm font-medium',
                    isActive
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:bg-accent/50'
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
            {!isAuthenticated && (
              <Button asChild size="sm" variant="outline" className="mt-2 w-full">
                <Link to="/login" onClick={() => setOpen(false)}>
                  <LogIn className="h-4 w-4" /> Войти
                </Link>
              </Button>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
