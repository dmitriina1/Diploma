import { Link } from 'react-router-dom'
import { Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { GridPattern } from '@/components/effects/grid-pattern'

export function NotFoundPage() {
  return (
    <div className="relative flex min-h-[60svh] flex-col items-center justify-center overflow-hidden px-4 py-20 text-center">
      <GridPattern
        width={36}
        height={36}
        className="[mask-image:radial-gradient(500px_circle_at_center,white,transparent)] -z-10"
        strokeDasharray="2 2"
      />
      <h1 className="text-7xl font-black gradient-text">404</h1>
      <p className="mt-2 text-lg font-medium">Страница не найдена</p>
      <p className="mt-1 text-sm text-muted-foreground">Проверьте URL или вернитесь на главную</p>
      <Button asChild className="mt-6" variant="gradient">
        <Link to="/">
          <Home className="h-4 w-4" /> На главную
        </Link>
      </Button>
    </div>
  )
}
