import { cn } from '@/lib/utils'

export function Meteors({ number = 20, className }: { number?: number; className?: string }) {
  const meteors = Array.from({ length: number }, (_, i) => i)
  return (
    <div className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}>
      {meteors.map((i) => (
        <span
          key={`meteor-${i}`}
          className="absolute h-0.5 w-0.5 rounded-full bg-primary shadow-[0_0_0_1px_#ffffff10] before:absolute before:left-0 before:top-1/2 before:h-px before:w-[60px] before:-translate-y-1/2 before:bg-gradient-to-r before:from-primary before:to-transparent"
          style={{
            top: `${Math.floor(Math.random() * 100)}%`,
            left: `${Math.floor(Math.random() * 100)}%`,
            animation: `meteor 5s linear ${Math.random() * 5}s infinite`,
            opacity: 0.4 + Math.random() * 0.6,
          }}
        />
      ))}
    </div>
  )
}
