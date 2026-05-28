import { Link } from 'react-router-dom'
import { Code, ExternalLink } from 'lucide-react'

export function Footer() {
  return (
    <footer className="mt-auto border-t border-border/60">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-4 px-4 py-8 sm:flex-row sm:items-center sm:px-6">
        <div className="flex flex-col gap-1">
          <span className="font-semibold">
            Interview<span className="gradient-text">Hub</span>
          </span>
          <p className="text-xs text-muted-foreground">
            Платформа подготовки к IT-собеседованиям на основе анализа видеоконтента
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
          <Link to="/interview-questions" className="hover:text-foreground transition-colors">
            Вопросы
          </Link>
          <Link to="/hh-requirements" className="hover:text-foreground transition-colors">
            HH-навыки
          </Link>
          <Link to="/suggest" className="hover:text-foreground transition-colors">
            Предложить
          </Link>
          <a
            href="/docs"
            className="hover:text-foreground transition-colors inline-flex items-center gap-1"
          >
            API <ExternalLink className="h-3 w-3" />
          </a>
          <a
            href="https://github.com/dmitriina1/Diploma"
            target="_blank"
            rel="noreferrer"
            className="hover:text-foreground transition-colors inline-flex items-center gap-1"
          >
            <Code className="h-3.5 w-3.5" /> GitHub
          </a>
        </div>
      </div>
    </footer>
  )
}
