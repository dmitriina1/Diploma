export interface User {
  id?: number
  username: string
  email?: string
  role: 'user' | 'admin'
  github_url?: string
  bio?: string
  created_at?: string
}

export interface Question {
  id: number
  text: string
  answer?: string | null
  source_type?: string
  source_url?: string | null
  difficulty?: number | null
  popularity?: number | null
  is_approved?: boolean
  tags?: string[]
  technology?: string | null
  profession?: string | null
  probability?: number | null
  created_at?: string
  videos?: ProcessedVideo[]
  user_answers_count?: number
}

export interface ProcessedVideo {
  id: number
  title: string
  url: string
  platform?: string
  channel?: string | null
  duration?: number | null
  thumbnail_url?: string | null
  created_at?: string
}

export interface ProcessingTask {
  task_id: string
  client_id: string
  url: string
  status: string
  progress?: number
  message?: string
  questions_count?: number
  error?: string | null
  started_at?: string
  finished_at?: string
  video_title?: string
}

export interface Profession {
  slug: string
  name: string
  questions_count?: number
  description?: string
}

export interface HHSkill {
  id?: number
  name: string
  count: number
  source: 'skills' | 'description' | 'title'
  profession_slug?: string
}

export interface TestAssignment {
  id: number
  title: string
  description?: string
  company?: string
  level?: string
  technology?: string
  body?: string
  url?: string | null
  created_at?: string
}

export interface Suggestion {
  id: number
  url: string
  description?: string
  status: 'pending' | 'approved' | 'rejected' | 'processing' | 'completed'
  user_session?: string
  created_at?: string
}

export interface MockInterviewSession {
  id?: number | string
  interview_id?: number | string
  title?: string
  level?: string
  questions?: Question[]
  score?: number | null
  status?: string
  created_at?: string
}

export interface InterviewChatSession {
  interview_id: string
  topic: string
  difficulty: string
  status?: string
  messages?: ChatMessage[]
  created_at?: string
}

export interface ChatMessage {
  id?: number | string
  role: 'user' | 'assistant'
  content: string
  created_at?: string
}

export interface SM2Card {
  id?: number
  question_id: number
  question_text?: string
  question?: Question
  ease_factor: number
  interval: number
  repetitions: number
  next_review_date: string
  last_grade?: number
  status?: 'new' | 'learning' | 'review' | 'mastered'
}

export interface PublicStats {
  questions_count?: number
  videos_count?: number
  professions_count?: number
  test_assignments_count?: number
  total_users?: number
  [key: string]: number | string | undefined
}

export interface AdminStats {
  questions_total?: number
  questions_pending?: number
  questions_approved?: number
  feedback_total?: number
  suggestions_pending?: number
  videos_total?: number
  [key: string]: number | string | undefined
}

export interface Feedback {
  id: number
  user_session?: string
  message: string
  status?: string
  page?: string
  created_at?: string
}
