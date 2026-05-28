import { Toaster as SonnerToaster } from 'sonner'
import { useTheme } from '@/hooks/use-theme'

export function Toaster() {
  const { resolvedTheme } = useTheme()
  return (
    <SonnerToaster
      theme={resolvedTheme}
      position="top-right"
      toastOptions={{
        classNames: {
          toast:
            'group toast bg-card text-card-foreground border border-border/60 shadow-md rounded-xl',
          description: 'text-muted-foreground',
          actionButton: 'bg-primary text-primary-foreground',
          cancelButton: 'bg-muted text-muted-foreground',
        },
      }}
    />
  )
}
