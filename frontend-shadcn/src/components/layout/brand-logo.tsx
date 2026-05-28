import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'

export function BrandLogo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <Link to="/" className={cn('group flex items-center gap-2 font-semibold', className)}>
      <span className="relative inline-flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 via-fuchsia-500 to-cyan-400 text-white shadow-md ring-1 ring-white/20 transition-transform group-hover:scale-105">
        <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4">
          <path
            d="M4 4l8 16 8-16M8 4l4 8 4-8"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      {!compact && (
        <span className="text-base font-bold tracking-tight">
          Interview<span className="gradient-text">Hub</span>
        </span>
      )}
    </Link>
  )
}
