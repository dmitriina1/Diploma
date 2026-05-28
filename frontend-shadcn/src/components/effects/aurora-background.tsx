import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface AuroraBackgroundProps {
  children: ReactNode
  className?: string
  showRadialGradient?: boolean
}

export function AuroraBackground({
  children,
  className,
  showRadialGradient = true,
}: AuroraBackgroundProps) {
  return (
    <div className={cn('relative isolate flex w-full flex-col overflow-hidden', className)}>
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div
          className={cn(
            'pointer-events-none absolute -inset-[10px] opacity-50 blur-[10px] will-change-transform',
            'after:absolute after:inset-0 after:[background-image:repeating-linear-gradient(100deg,var(--white)_0%,var(--white)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--white)_16%)] after:[background-size:200%,_100%] after:[background-attachment:fixed] after:mix-blend-difference after:content-[""]',
            'animate-aurora',
            'dark:opacity-50',
            '[--white:#ffffff]',
            '[--transparent:transparent]',
            '[background-image:repeating-linear-gradient(100deg,#a78bfa_10%,#7c3aed_15%,#06b6d4_20%,#3b82f6_25%,#7c3aed_30%)] [background-size:300%,_200%] [background-position:50%_50%,50%_50%]'
          )}
        />
        {showRadialGradient && (
          <div className="pointer-events-none absolute inset-0 bg-background [mask-image:radial-gradient(ellipse_at_100%_0%,transparent_10%,black_70%)] dark:[mask-image:radial-gradient(ellipse_at_100%_0%,transparent_10%,black_70%)]" />
        )}
      </div>
      {children}
    </div>
  )
}
