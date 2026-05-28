import { Outlet } from 'react-router-dom'
import { NavBar } from './navbar'
import { Footer } from './footer'

export function AppLayout() {
  return (
    <div className="relative flex min-h-svh flex-col">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[420px] bg-gradient-to-b from-primary/10 via-primary/5 to-transparent dark:from-primary/15" />
      <NavBar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
