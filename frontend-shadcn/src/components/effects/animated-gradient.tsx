import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function AnimatedGradientText({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-block bg-gradient-to-r from-violet-500 via-cyan-400 to-violet-500 bg-[length:200%_auto] bg-clip-text text-transparent animate-shimmer',
        className
      )}
    >
      {children}
    </span>
  )
}
